"""Trusted VIP circle (spec §3.13 B + B2 v5): live drop-ins, knocks, async notes/pins, revocation.

Every check is enforced here in the backend, never by prompt instructions.
A VIP acts either as a signed-in user (MCP) or through their private VIP link token (web).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select

from .app import App, Ctx
from .characters import COMMENTATORS, JOIN_POLICIES
from .common import (
    LinkInactive,
    LoungeError,
    clean_handle,
    clean_text,
    find_user,
    get_or_create_lounge,
    get_or_create_user,
    line_dicts,
    narrate,
    notify,
    open_presence,
    owner_presence,
    take_notices,
    theme_info,
    touch,
    vip_presence,
    wall,
)
from .content import ContentService
from .events import EventType, emit
from .gallery import ExchangePlan
from .models import Decoration, Discovery, Knock, Lounge, Note, Presence, SeenDiscovery, User, Utterance, VipLinkUse, VipRelationship


@dataclass
class VipActor:
    rel: VipRelationship
    owner: User
    lounge: Lounge
    user: User | None  # None when acting through the VIP link


class VipService:
    def __init__(self, app: App):
        self.app = app

    # ------------------------------------------------------------------ owner side
    def invite(self, owner_handle: str, label: str, display_name: str | None = None, *,
               can_drop_in: bool = True, can_leave_note: bool = True, can_pin_to_wall: bool = True) -> dict:
        with self.app.ctx() as c:
            owner = get_or_create_user(c, owner_handle)
            get_or_create_lounge(c, owner)
            label = clean_text(label, 60).lower()
            if c.s.scalar(select(VipRelationship).where(VipRelationship.owner_id == owner.id, VipRelationship.label == label, VipRelationship.status != "revoked")):
                raise LoungeError(f"You already have an active VIP called “{label}”.")
            rel = VipRelationship(
                owner_id=owner.id,
                label=label,
                display_name=clean_text(display_name or label.title(), 60),
                invite_code=secrets.token_hex(4).upper(),
                link_token=secrets.token_urlsafe(24),
                can_drop_in=can_drop_in,
                can_leave_note=can_leave_note,
                can_pin_to_wall=can_pin_to_wall,
                created_at=c.now(),
            )
            c.s.add(rel)
            c.s.flush()
            emit(c.s, EventType.VIP_INVITED, actor_type="human_owner", actor_id=owner.handle, payload={"rel_id": rel.id, "label": label}, at=c.now())
            link = f"{self.app.settings.web_base_url.rstrip('/')}/v/{rel.link_token}"
            return {
                "label": rel.label,
                "name": rel.display_name,
                "invite_code": rel.invite_code,
                "vip_link": link,
                "permissions": self._perms(rel),
                "narration": (
                    f"Invited {rel.display_name} as your {rel.label}. Send them either the code {rel.invite_code} "
                    f"(if they use an AI assistant with this lounge connected) or their private link: {link}\n"
                    f"Your lounge's door is set to “{get_or_create_lounge(c, owner).join_policy}”. "
                    "Set it to open or knock if you want them to be able to drop in."
                ),
            }

    @staticmethod
    def _perms(rel: VipRelationship) -> dict:
        return {"drop_in": rel.can_drop_in, "leave_note": rel.can_leave_note, "pin_to_wall": rel.can_pin_to_wall}

    def list(self, owner_handle: str) -> dict:
        with self.app.ctx() as c:
            owner = get_or_create_user(c, owner_handle)
            rels = c.s.scalars(select(VipRelationship).where(VipRelationship.owner_id == owner.id).order_by(VipRelationship.id)).all()
            out = [{"label": r.label, "name": r.display_name, "status": r.status, "permissions": self._perms(r)} for r in rels]
            text = "\n".join(f"- {r['name']} (your {r['label']}): {r['status']}" for r in out) or "You haven't invited anyone yet."
            return {"vips": out, "narration": text}

    def set_join_policy(self, owner_handle: str, policy: str) -> dict:
        if policy not in JOIN_POLICIES:
            raise LoungeError(f"Policy must be one of: {', '.join(JOIN_POLICIES)}.")
        with self.app.ctx() as c:
            owner = get_or_create_user(c, owner_handle)
            lounge = get_or_create_lounge(c, owner)
            lounge.join_policy = policy
            emit(c.s, EventType.JOIN_POLICY, actor_type="human_owner", actor_id=owner.handle, lounge_id=lounge.id, payload={"policy": policy}, at=c.now())
            meaning = {
                "open": "approved VIPs can drop in any time",
                "knock": "approved VIPs knock and you decide",
                "private": "nobody drops in (they can still leave notes)",
            }[policy]
            return {"join_policy": policy, "narration": f"Door set to {policy}: {meaning}."}

    def revoke(self, owner_handle: str, label: str) -> dict:
        with self.app.ctx() as c:
            owner = get_or_create_user(c, owner_handle)
            lounge = get_or_create_lounge(c, owner)
            rel = c.s.scalar(select(VipRelationship).where(
                VipRelationship.owner_id == owner.id, VipRelationship.label == label.strip().lower(), VipRelationship.status != "revoked"))
            if rel is None:
                raise LoungeError(f"No active VIP called “{label}”.")
            rel.status = "revoked"
            rel.revoked_at = c.now()
            p = vip_presence(c, lounge, rel)
            if p:
                p.left_at = c.now()
            for k in c.s.scalars(select(Knock).where(Knock.vip_relationship_id == rel.id, Knock.status == "pending")):
                k.status, k.resolved_at = "declined", c.now()
            emit(c.s, EventType.VIP_REVOKED, actor_type="human_owner", actor_id=owner.handle, lounge_id=lounge.id, payload={"rel_id": rel.id}, at=c.now())
            return {"revoked": rel.label, "narration": f"{rel.display_name}'s access is revoked. Their code and link no longer work."}

    def answer_knock(self, owner_handle: str, knock_id: int, admit: bool) -> dict:
        with self.app.ctx() as c:
            owner = get_or_create_user(c, owner_handle)
            lounge = get_or_create_lounge(c, owner)
            k = c.s.get(Knock, knock_id)
            if k is None or k.lounge_id != lounge.id or k.status != "pending":
                raise LoungeError("No such pending knock.")
            rel = c.s.get(VipRelationship, k.vip_relationship_id)
            if rel.status == "revoked":
                raise LoungeError("That person's access was revoked.")
            k.status, k.resolved_at = ("admitted" if admit else "declined"), c.now()
            emit(c.s, EventType.VIP_KNOCK_ANSWERED, actor_type="human_owner", actor_id=owner.handle, lounge_id=lounge.id, payload={"knock_id": k.id, "admitted": admit}, at=c.now())
            if not admit:
                notify(c, rel.vip_user_id, f"{owner.handle} can't have visitors right now.")
                return {"admitted": False, "narration": f"You let {rel.display_name} know it's not a good time."}
            actor = VipActor(rel=rel, owner=owner, lounge=lounge, user=c.s.get(User, rel.vip_user_id) if rel.vip_user_id else None)
            lines = self._join(c, actor)
            notify(c, rel.vip_user_id, f"{owner.handle} let you in.")
            return {"admitted": True, "conversation": line_dicts(lines), "narration": narrate(lines)}

    # ------------------------------------------------------------------ VIP side: resolving who they are
    def accept(self, vip_handle: str, invite_code: str) -> dict:
        with self.app.ctx() as c:
            vip_user = get_or_create_user(c, vip_handle)
            rel = c.s.scalar(select(VipRelationship).where(VipRelationship.invite_code == (invite_code or "").strip().upper()))
            if rel is None or rel.status == "revoked":
                raise LoungeError("That invite code isn't valid.")
            if rel.owner_id == vip_user.id:
                raise LoungeError("You can't accept your own invite.")
            if rel.vip_user_id not in (None, vip_user.id):
                raise LoungeError("That invite was already accepted by someone else.")
            rel.vip_user_id = vip_user.id
            rel.status = "active"
            rel.accepted_at = rel.accepted_at or c.now()
            owner = c.s.get(User, rel.owner_id)
            emit(c.s, EventType.VIP_ACCEPTED, actor_type="human_vip", actor_id=vip_user.handle, payload={"rel_id": rel.id}, at=c.now())
            return {"owner": owner.handle, "you_are_their": rel.label, "narration": f"You're on {owner.handle}'s VIP list now. Visit with: visit_lounge(owner=\"{owner.handle}\")."}

    def my_lounges(self, vip_handle: str) -> dict:
        with self.app.ctx() as c:
            vip_user = get_or_create_user(c, vip_handle)
            rels = c.s.scalars(select(VipRelationship).where(VipRelationship.vip_user_id == vip_user.id, VipRelationship.status == "active")).all()
            out = []
            for r in rels:
                owner = c.s.get(User, r.owner_id)
                lounge = get_or_create_lounge(c, owner)
                out.append({"owner": owner.handle, "you_are_their": r.label, "door": lounge.join_policy, "permissions": self._perms(r)})
            return {"lounges": out, "notices": take_notices(c, vip_user),
                    "narration": "\n".join(f"- {o['owner']} (door: {o['door']})" for o in out) or "Nobody has added you as a VIP yet."}

    def _actor_by_user(self, c: Ctx, vip_handle: str, owner_handle: str) -> VipActor:
        vip_user = get_or_create_user(c, vip_handle)
        owner = find_user(c, clean_handle(owner_handle))
        rel = None
        if owner is not None:
            rel = c.s.scalar(select(VipRelationship).where(
                VipRelationship.owner_id == owner.id, VipRelationship.vip_user_id == vip_user.id, VipRelationship.status == "active"))
        if rel is None:
            # Same message whether the lounge doesn't exist or you're not approved: no probing.
            emit(c.s, EventType.VIP_DENIED, actor_type="system", actor_id="vip", payload={"by": vip_user.handle, "reason": "not_approved"}, at=c.now())
            raise LoungeError("You're not on that person's VIP list.")
        return VipActor(rel=rel, owner=owner, lounge=get_or_create_lounge(c, owner), user=vip_user)

    def _actor_by_link(self, c: Ctx, token: str) -> VipActor:
        rel = c.s.scalar(select(VipRelationship).where(VipRelationship.link_token == token))
        if rel is None or rel.status == "revoked":
            raise LinkInactive("This link isn't active.")
        if rel.status == "invited":  # opening the private link is accepting the invite
            rel.status = "active"
            rel.accepted_at = c.now()
            emit(c.s, EventType.VIP_ACCEPTED, actor_type="human_vip", actor_id=f"link:{rel.id}", payload={"rel_id": rel.id, "via": "link"}, at=c.now())
        recent = c.s.scalars(select(VipLinkUse).where(VipLinkUse.vip_relationship_id == rel.id, VipLinkUse.created_at > c.now() - timedelta(hours=1))).all()
        if len(recent) >= self.app.settings.vip_link_actions_per_hour:
            raise LoungeError("That's a lot of activity for one hour — try again a bit later.")
        owner = c.s.get(User, rel.owner_id)
        return VipActor(rel=rel, owner=owner, lounge=get_or_create_lounge(c, owner), user=c.s.get(User, rel.vip_user_id) if rel.vip_user_id else None)

    def _vip_payload(self, actor: VipActor, **extra) -> dict:
        return {"rel_id": actor.rel.id, "name": actor.rel.display_name, "label": actor.rel.label, **extra}

    def _actor_id(self, actor: VipActor) -> str:
        return actor.user.handle if actor.user else f"link:{actor.rel.id}"

    # ------------------------------------------------------------------ VIP actions
    def drop_in(self, vip_handle: str, owner_handle: str) -> dict:
        with self.app.ctx() as c:
            actor = self._actor_by_user(c, vip_handle, owner_handle)
            rel, lounge = actor.rel, actor.lounge
            if not rel.can_drop_in:
                raise LoungeError("You can leave notes, but drop-ins aren't enabled for you.")
            if vip_presence(c, lounge, rel):
                raise LoungeError("You're already there.")
            if lounge.join_policy == "private":
                emit(c.s, EventType.VIP_DENIED, actor_type="human_vip", actor_id=self._actor_id(actor), lounge_id=lounge.id, payload=self._vip_payload(actor, reason="private"), at=c.now())
                return {"status": "private", "narration": f"{actor.owner.handle}'s door is closed right now. You can still leave a note."}
            if lounge.join_policy == "knock":
                k = Knock(lounge_id=lounge.id, vip_relationship_id=rel.id, created_at=c.now())
                c.s.add(k)
                c.s.flush()
                emit(c.s, EventType.VIP_KNOCKED, actor_type="human_vip", actor_id=self._actor_id(actor), lounge_id=lounge.id, payload=self._vip_payload(actor, knock_id=k.id), at=c.now())
                if owner_presence(c, lounge):
                    notify(c, actor.owner.id, f"{rel.display_name} (your {rel.label}) is knocking. Answer with answer_knock(knock_id={k.id}).")
                return {"status": "knocked", "knock_id": k.id, "narration": "You knocked. They'll let you in if they can."}
            lines = self._join(c, actor)
            return {"status": "joined", "conversation": line_dicts(lines, viewer="vip"), "narration": self._vip_scene(c, actor) + "\n\n" + narrate(lines, viewer="vip"),
                    "notices": take_notices(c, actor.user) if actor.user else []}

    def _join(self, c: Ctx, actor: VipActor) -> list[Utterance]:
        rel, lounge = actor.rel, actor.lounge
        now = c.now()
        c.s.add(Presence(lounge_id=lounge.id, user_id=actor.user.id if actor.user else None, vip_relationship_id=rel.id,
                         role="vip", display_name=rel.display_name, joined_at=now, last_active_at=now))
        for k in c.s.scalars(select(Knock).where(Knock.vip_relationship_id == rel.id, Knock.status == "pending")):
            k.status, k.resolved_at = "admitted", now  # they're in now; an older knock is moot
        emit(c.s, EventType.VIP_JOINED, actor_type="human_vip", actor_id=self._actor_id(actor), lounge_id=lounge.id, payload=self._vip_payload(actor), at=now)
        owner_here = owner_presence(c, lounge) is not None
        if owner_here:  # visible arrivals: no stealth joins
            notify(c, actor.owner.id, f"{rel.display_name} (your {rel.label}, human) just walked in.")
        d = c.s.get(Discovery, lounge.current_discovery_id) if lounge.current_discovery_id else None
        plan = ExchangePlan(
            kind="vip_greeting", lounge=lounge, owner=actor.owner, discovery=d, vip_present=True,
            host_facts={"vip_name": rel.display_name, "owner_present": owner_here, "owner_name": actor.owner.handle},
            max_commentator_turns=1, include_owner_memory=False,  # never expose the owner's private memories to a guest
        )
        return c.gallery.run(plan)

    def say(self, vip_handle: str, owner_handle: str, text: str) -> dict:
        with self.app.ctx() as c:
            actor = self._actor_by_user(c, vip_handle, owner_handle)
            p = vip_presence(c, actor.lounge, actor.rel)
            if p is None:
                raise LoungeError("You're not in their lounge right now. Drop in first.")
            touch(c, p)
            d = c.s.get(Discovery, actor.lounge.current_discovery_id) if actor.lounge.current_discovery_id else None
            u = Utterance(exchange_id=None, lounge_id=actor.lounge.id, speaker_type="human_vip", speaker_key=f"vip:{actor.rel.id}",
                          speaker_name=actor.rel.display_name, text=clean_text(text, 1000), created_at=c.now())
            plan = ExchangePlan(kind="reply", lounge=actor.lounge, owner=actor.owner, discovery=d, human_line=u, vip_present=True,
                                speaker_name_for_human=actor.rel.display_name, max_commentator_turns=2, include_owner_memory=False)
            lines = c.gallery.run(plan)
            emit(c.s, EventType.VIP_SPOKE, actor_type="human_vip", actor_id=self._actor_id(actor), lounge_id=actor.lounge.id,
                 payload=self._vip_payload(actor, utterance_id=u.id, presence_id=p.id), at=c.now())
            owner_p = owner_presence(c, actor.lounge)
            if owner_p is not None:
                notify(c, actor.owner.id, f"{actor.rel.display_name} said: “{u.text[:200]}”")
            return {"conversation": line_dicts(lines, viewer="vip"), "narration": narrate(lines, viewer="vip")}

    def leave(self, vip_handle: str, owner_handle: str) -> dict:
        with self.app.ctx() as c:
            actor = self._actor_by_user(c, vip_handle, owner_handle)
            p = vip_presence(c, actor.lounge, actor.rel)
            if p is None:
                raise LoungeError("You're not there.")
            self._close_visit(c, actor, p)
            return {"narration": "You head out. They'll know you stopped by."}

    def _close_visit(self, c: Ctx, actor: VipActor, p: Presence) -> None:
        now = c.now()
        p.left_at = now
        # Summarise only what actually happened during this visit.
        lines = c.s.scalars(select(Utterance).where(Utterance.lounge_id == actor.lounge.id, Utterance.created_at >= p.joined_at).order_by(Utterance.id)).all()
        chatted = sorted({u.speaker_name for u in lines if u.speaker_type == "bot" and u.speaker_key in {x.key for x in COMMENTATORS}})
        mine = [u for u in lines if u.speaker_type == "human_vip" and u.speaker_key == f"vip:{actor.rel.id}"]
        d = c.s.get(Discovery, actor.lounge.current_discovery_id) if actor.lounge.current_discovery_id else None
        payload = self._vip_payload(
            actor,
            presence_id=p.id,
            shared=actor.rel.share_visit_with_owner,
            chatted_with=chatted if mine else [],
            topic=d.title if (d and mine) else None,
            highlight=mine[0].text[:160] if mine else None,
        )
        emit(c.s, EventType.VIP_LEFT, actor_type="human_vip", actor_id=self._actor_id(actor), lounge_id=actor.lounge.id, payload=payload, at=now)
        if owner_presence(c, actor.lounge):
            notify(c, actor.owner.id, f"{actor.rel.display_name} headed out.")

    def leave_note(self, vip_handle: str | None, owner_handle: str | None, text: str, *, link_token: str | None = None) -> dict:
        with self.app.ctx() as c:
            actor = self._actor_by_link(c, link_token) if link_token else self._actor_by_user(c, vip_handle, owner_handle)
            if not actor.rel.can_leave_note:
                raise LoungeError("Notes aren't enabled for you.")
            text = clean_text(text, 500)
            n = Note(lounge_id=actor.lounge.id, vip_relationship_id=actor.rel.id, text=text, created_at=c.now())
            c.s.add(n)
            c.s.flush()
            if link_token:
                c.s.add(VipLinkUse(vip_relationship_id=actor.rel.id, created_at=c.now()))
            emit(c.s, EventType.VIP_NOTE, actor_type="human_vip", actor_id=self._actor_id(actor), lounge_id=actor.lounge.id, payload=self._vip_payload(actor, note_id=n.id, text=text), at=c.now())
            if owner_presence(c, actor.lounge):
                notify(c, actor.owner.id, f"{actor.rel.display_name} left you a note: “{text}”")
            return {"note_id": n.id, "narration": "Note left. Wren will make sure they get it."}

    def shareable(self, c: Ctx, actor: VipActor) -> list[Discovery]:
        """Discoveries a guest may pin: ones already shown in the owner's lounge (titles only, no conversation)."""
        q = (select(Discovery).join(SeenDiscovery, SeenDiscovery.discovery_id == Discovery.id)
             .where(SeenDiscovery.user_id == actor.owner.id).order_by(SeenDiscovery.seen_at.desc()).limit(10))
        return list(c.s.scalars(q))

    def pin(self, vip_handle: str | None, owner_handle: str | None, *, discovery_id: int | None = None, label: str | None = None,
            spot: str | None = None, link_token: str | None = None) -> dict:
        with self.app.ctx() as c:
            actor = self._actor_by_link(c, link_token) if link_token else self._actor_by_user(c, vip_handle, owner_handle)
            if not actor.rel.can_pin_to_wall:
                raise LoungeError("Pinning isn't enabled for you.")
            d = None
            if discovery_id is not None:
                d = next((x for x in self.shareable(c, actor) if x.id == discovery_id), None)
                if d is None:
                    raise LoungeError("You can pin discoveries from their lounge, or a keepsake with a label.")
            elif not label:
                raise LoungeError("Give a discovery id or a label.")
            t = theme_info(actor.lounge)
            dec = Decoration(lounge_id=actor.lounge.id, label=clean_text(label, 200) if label else d.title,
                             spot=clean_text(spot, 120) if spot else t["spots"][1 % len(t["spots"])],
                             kind="discovery_pin" if d else "keepsake", discovery_id=d.id if d else None,
                             placed_by_vip_id=actor.rel.id, created_at=c.now())
            c.s.add(dec)
            c.s.flush()
            if link_token:
                c.s.add(VipLinkUse(vip_relationship_id=actor.rel.id, created_at=c.now()))
            emit(c.s, EventType.VIP_PINNED, actor_type="human_vip", actor_id=self._actor_id(actor), lounge_id=actor.lounge.id,
                 payload=self._vip_payload(actor, decoration_id=dec.id, item=dec.label, spot=dec.spot), at=c.now())
            if owner_presence(c, actor.lounge):
                notify(c, actor.owner.id, f"{actor.rel.display_name} pinned “{dec.label}” {dec.spot}.")
            return {"pinned": {"id": dec.id, "label": dec.label, "spot": dec.spot}, "narration": f"Pinned “{dec.label}” {dec.spot}."}

    # ------------------------------------------------------------------ what a guest may see
    def _vip_scene(self, c: Ctx, actor: VipActor) -> str:
        t = theme_info(actor.lounge)
        here = [f"{p.display_name} (human)" for p in open_presence(c, actor.lounge) if p.vip_relationship_id != actor.rel.id]
        bits = [f"[{actor.owner.handle}'s place: {t['name']} — {t['description']}]"]
        items = wall(c, actor.lounge)
        if items:
            bits.append("On the wall: " + "; ".join(f"“{w['label']}” {w['spot']}" for w in items) + ".")
        bits.append("Here: Wren, Theo, Jules, Pip (AI regulars)" + (", " + ", ".join(here) if here else "") + ".")
        return "\n".join(bits)

    def link_view(self, token: str) -> dict:
        """What the lightweight VIP link page may show: the wall and shareable discovery titles. Nothing else."""
        with self.app.ctx() as c:
            actor = self._actor_by_link(c, token)
            return {
                "owner": actor.owner.handle,
                "you_are_their": actor.rel.label,
                "your_name": actor.rel.display_name,
                "setting": theme_info(actor.lounge)["name"],
                "wall": [{"label": w["label"], "spot": w["spot"]} for w in wall(c, actor.lounge)],
                "shareable": [{"id": d.id, "title": d.title, "url": d.canonical_url} for d in self.shareable(c, actor)] if actor.rel.can_pin_to_wall else [],
                "can_note": actor.rel.can_leave_note,
                "can_pin": actor.rel.can_pin_to_wall,
            }
