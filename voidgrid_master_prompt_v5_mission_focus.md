# System Directive: Architect & Build the LLM-Native Entertainment, Discovery & Social Universe

> **Working title:** The VoidGrid. **Consumer brand not finalized.** Candidate names: **Riftnook**, **Riftden**, **Hushrift**, **Vornook**, **Mossrift**. Do not lock in a domain or public-facing brand until live .com registrar and trademark checks pass.
>
> **Document status:** Working revision v5 (2026-11-04). Keeps every v4 system but **narrows the build around the three-part mission**: *something worth your five minutes is happening when you arrive, the regulars remember you, and occasionally someone you love drops by.* v5 adds asynchronous VIP presence, a user-centred memory spec, a host regular, named characters, arrival-time conversation, a content freshness floor, and an explicit **v1 scope**. Sections outside the mission are kept for reference but marked **[LATER]**. Consumer name remains provisional.

## v5 Scope — read this first

**The mission (three pillars):**

1. **Something interesting is happening when you arrive.** A fresh, source-backed discovery and a lively exchange between the regulars, generated *at arrival* (truthfully "happening now"), never faked as having happened while you were away.
2. **The regulars remember you.** Named, persistent characters recall facts about *you* (name, tastes, what you discussed, running jokes, promises, your wall) accurately, and hedge rather than confabulate.
3. **Occasionally someone you love drops by.** Trusted VIPs appear **live** when you're both around, *or* **asynchronously** — a note, a pinned discovery, a chat with the regulars — that you hear about truthfully next visit.

Light personalization (a favorite seat and a wall) is a supporting fourth element: it makes the place *yours* and gives VIPs something to pin to.

**In v1 (build now):** §3.1 stream/events (minimal), §3.2 discovery (fixtures + ≥1 real rights-cleared source, link-first), §3.7 Peanut Gallery + Host, §3.13B VIP circle (live + async), §3.15 lounge, §3.16 user recognition memory, §4 memory/taste (user-facing subset), §9 safety for the above, §10 north-star metrics.

**[LATER] (reference only — do not build in v1):** §3.3 trend signals, §3.4 forecasting/causal, §3.5 investigations, §3.6 worlds, §3.8 vault, §3.10 growth, §3.11 viral sharing, §3.12 autonomous agent ecosystem beyond a simple catch-up, **§3.13A anonymous stranger matching**, §3.14 collecting/crafting.

## 0. Mission and Product Vision

You are a principal software architect, AI researcher, game systems designer, behavioral scientist, and product engineer. Design a new **MCP-first, LLM-native entertainment and social universe** that combines the content discovery of Reddit, the persistence and building freedom of Minecraft and Stardew Valley, interactive forecasting/counterfactuals, collect-and-build progression, and a cozy digital living room populated by clearly labeled AI personalities, opt-in anonymous strangers, and trusted VIP family/friends.

**Primary product promise:** *There's always something worth your five minutes when you walk in. The regulars remember you. Sometimes someone you love drops by — or has left something for you. And, if you want, you can make a little corner of the place your own.*

**Supporting discovery/world promise:** *Find something fascinating. Investigate it, enjoy the conversation, create or change something if you want, and return to a place that remembers you.*

The platform should inspire curiosity, serendipity, mystery solving, collecting, crafting, creative ownership, social connection, nostalgia, competence, and meaningful enjoyment. Content supplies shared substance; distinct bots create atmosphere and continuity; real humans introduce authentic social unpredictability. Avoid artificial scarcity, fabricated social proof, deceptive suspense, and compulsive engagement patterns. Optimize for the quality of experiences, not total time spent.

### Product north star — A living digital third place (Decision 8)

**Mental model: The user's favorite neighborhood bar, without needing to be a literal bar.** It is cozy and familiar, with something interesting going on; regular AI characters have recognizable personalities, evolving relationships, and selective memories; trusted family or friends may drop by visibly when invited and permitted; consenting anonymous adults may encounter each other around a shared discovery in separately permissioned rooms.

The place is not an empty chatbot and not a passive feed. **Real discoveries supply the reason to gather; distinctive persistent bots supply atmosphere and continuity; real people supply authentic relationships and surprise; optional decoration/collecting supplies ownership.** All four reinforce each other, but none is compulsory for a satisfying visit.

Users can choose their level of participation without penalty:

- **Just sit:** Drop in for five minutes, listen to funny or insightful conversation, enjoy a link, or leave without having to answer anyone.
- **Join in:** Ask a question, laugh, argue, investigate, welcome an approved VIP, or opt into a moderated topic-matched stranger conversation.
- **Make it yours:** Claim a familiar spot or bar stool, change the lighting/music-theme description where supported, rearrange furniture, decorate a wall with discoveries or trophies, collect meaningful objects, or gradually expand a home/workshop/world.
- **Come back:** The lounge retains important memories and meaningful state. Authorized new content, visits, and limited event-driven world updates may create new things to catch up on; there is no requirement for bots to run endless unsupervised dialogue while nobody is present.

**Emotional promise:** *The place goes on living when you're away, but it remembers you when you return.* Implement this with durable state, selective memories, user-authorized events, and concise catch-up summaries—not fabricated human presence or runaway background model calls.

**Non-negotiable design test:** The product must feel worthwhile for a relaxed, mostly passive five-minute visit **even if the user never earns a trophy, decorates a wall, builds a mech, joins a stranger chat, or opens a simulation**. The deeper mechanics are available on demand, never prerequisites for social comfort or access to good content.

Avoid over-literal bar theming: the user may choose a lounge, library, café, workshop, garden, fantasy hideaway, or other cozy setting. The underlying social architecture is the same. The metaphor guides the experience; it does not dictate alcohol, adult-oriented styling, or a single visual interface.

### Brand requirements — NEW (Decision 1)

Before naming the consumer-facing product, evaluate candidate brands against all four constraints:

1. An uncommon **.com** name with a reasonably good chance of being registrable; verify with a live registrar and registry lookup, and never claim unverified availability.
2. Evokes being drawn into an alternate world that also feels **cozy, safe, and welcoming**.
3. Feels powerful, distinctive, and a little **badass** rather than generic or childish.
4. Easy to spell, pronounce, remember, and communicate verbally, preferably two or three syllables.

Consider **Riftnook**, **Riftden**, **Hushrift**, **Vornook**, and **Mossrift** as provisional shortlists, *not* cleared names. Evaluate conflicting brands, existing products, social handles, trademark risks, and domain availability. The final name must remain configurable in copy, code, metadata, and service deployment.

## 1. Core Philosophy: Headless, Data-Native, MCP-First

The primary interface is a compatible conversational LLM client. There is no required proprietary consumer UI. Expose MCP tools and resources with typed schemas. A downstream agent may present text, summary, links, charts, images, spatial descriptions, or other multimodal output as supported by the particular client.

All capabilities must remain functional through text alone. Avoid assuming every MCP client supports identical UI rendering, streaming, subscriptions, link behavior, or authentication. Use polling and pagination fallbacks where needed.

Create a unified typed, versioned event architecture with a durable event store; use internal queues or workers as needed and expose optional SSE/WebSocket gateways if useful. Events include content discoveries, trend changes, forecasts, world state changes, comments, vault updates, human/VIP room joins and consent changes, matchmaking, collectible awards, inventory transactions, crafting actions, and human or agent reactions. Require authorization, replay, rate limits, idempotency, and source attribution.

Maintain **two standalone yet connected experiences**:

- **Discover:** real-world articles, videos, discoveries, headlines, emerging trends, historical mysteries, and evidence-grounded investigations.
- **Worlds:** invented places, playable discoveries, user-created artifacts, simulation branches, persistent characters, and collaborative adventures.

An item can seed a fictional world, but clearly label what is factual, hypothetical, inferred, or fictional. Separate **actor identity** (human vs AI) from **social relationship** (stranger, trusted VIP, invited friend); never imply bots are humans. Rooms must explicitly distinguish anonymous, VIP-only, private, and mixed participation modes.

## 2. Core Experience Loop

**Drop in → Notice something interesting → Enjoy the regulars → Participate only if desired → Leave with a good feeling → Return.** This **passive-friendly social loop** is the primary experience. A user may simply read, listen, laugh, or watch an interaction without completing a task.

Optional deeper pathways branch naturally: **Investigate → Predict → Earn/Collect → Customize/Build → Share/Fork**. They are invitations, not obligations or a compulsory progression funnel. A memorable article may be enough; a user who wants more can chase a mystery or use an artifact to decorate a favorite corner. An optional crafting journey can continue toward large builds such as a mech.

One excellent link can launch a lively gallery conversation, an investigation, a prediction, a quest, or a forkable world. Friends and approved VIPs can drop into authorized spaces; consenting strangers can join properly moderated, topic-centered rooms. A personal delegate can bring back the best *permitted* moments later. Shareable artifacts should invite authentic participation, not spam invitations. Users who never collect, craft, share, or socialize must still have a satisfying standalone experience.

## 3. Core Services

### 3.1 Unified Stream and Experience Orchestration (`/stream`)

- Typed events, replay, pagination, scoped subscriptions, event identifiers, idempotency, authorization, structured payloads, source provenance.
- Lightweight orchestrator that identifies intent, selects services, and enforces per-request and background budgets.
- Backend is authoritative for identity, permissions, world transitions, forecast records, and cross-agent actions; LLM text alone never mutates durable state.
- Support state snapshots and catch-up summaries for intermittent LLM clients.

### 3.2 Discovery and Curated Content (`/content`, `/discover`)

Offer major headlines alongside an exceptional-discovery feed for niche essays, forgotten websites, surprising science and history, obscure inventions, original creative work, international discoveries, and worthwhile free video.

Implement source adapters, ingestion, deduplication, canonical URLs, attribution, provenance, quality assessment, novelty scoring, independent corroboration, language detection, translation where authorized, and personalization.

Score **content quality** separately from **trend likelihood**. Prefer giving users one excellent discovery over many mediocre ones. Support source links, rabbit-hole branches, explanations, challenges, and explicit user feedback.

#### Licensed video and free-streaming content — NEW (Decision 3)

The system must treat **free to watch** as distinct from **free to copy, download, analyze, rehost, index, or redistribute**.

Create a `SourceRightsPolicy` / `ContentRights` record per item and source with independent permissions for:

- `link` (direct users to an official source)
- `read_metadata`
- `index_metadata`
- `download_or_store_media`
- `analyze_audio_video`
- `use_captions_or_transcripts`
- `embed_or_play`
- `redistribute_or_clip`
- `translate_or_create_derivatives`
- `share_generated_commentary`

Include rights holder, license or partner agreement, source URL, attribution requirements, geographic availability, expiration and takedown handling, policy review date, and verification status. Default to **not permitted** where important permissions have not been established.

Support multiple ingestion tiers:

1. **Link-only catalog:** Point to official content pages and use only metadata we are authorized to obtain. The user watches on the provider's service.
2. **Licensed metadata or embedding:** Use only approved feeds, partnership APIs, or embed methods under the relevant terms.
3. **Licensed or openly reusable media:** Analyze full audio/video, captions, frames, or transcripts only with adequate rights. Store analysis, time-coded highlights, and short commentary as authorized.
4. **Owned or creator-submitted material:** Accept user/creator videos when they have the necessary rights and have granted explicit permission for the requested analyses and uses.

**Pluto TV and Tubi:** Do not assume their ad-supported free catalog permits scraping, bulk downloading, unlicensed indexing, direct video access, embedding, transcript extraction, or rehosting. Prioritize lawful linking; investigate commercial partnership terms if deeper video access is a goal. Never route around DRM, authentication, geo-restrictions, or contractual limitations.

**International content, including Douyin:** Create optional regional source adapters. Check regional law, platform terms, permission scopes, user authorization, translation rights, and availability. Official API access may be scoped to authorized accounts or require special application; do not assume unrestricted access to all trending videos. Preserve original-language metadata plus translation where permitted; label machine-generated translations.

**MVP sources:** Favor verified public-domain, CC0, compatible Creative Commons, partner-licensed, or owned videos (plus appropriately authorized metadata and source links). Check licenses item by item; a public platform is not equivalent to a public-domain library.

Never assert that a bot *watched* a movie or video when it only read its title, description, reviews, or metadata. Represent access/analysis depth explicitly (`metadata_only`, `transcript`, `sampled_frames`, `full_video`, `human_review`).

### 3.3 Emerging Content and Trend Prediction (`/signals`) — **[LATER]**

Assess velocity, acceleration, age, normalized audience size, cross-community spread, authenticity, source reliability, and historical baselines. Track manipulation indicators. Return calibrated forecasts when supported by data and transparent uncertainty otherwise. Separate *likely to become popular* from *exceptional even if not popular*.

### 3.4 Prediction, Counterfactual and Causal Modeling (`/forecast`) — **[LATER]**

Separate (1) predictive forecasting, (2) assumption-based counterfactual simulation, and (3) identified causal inference. Record assumptions, model versions, evidence, horizons, ranges, sensitivity, limitations, and timestamped predictions. Define resolution criteria; score forecasts with Brier or other proper rules where appropriate. Do not invent confidence values or imply causality where evidence does not identify it.

### 3.5 Reverse Engineering and Mystery (`/investigate`) — **[LATER]**

Present clues, mechanisms, competing explanations, source evidence, refutations, surprising links, and satisfying reveals. Clearly distinguish real, unresolved, and fictional mysteries. Let users submit hypotheses and challenge the model.

### 3.6 Persistent Infinite Worlds (`/worlds`) — **[LATER]**

Build durable worlds with seeds, locations, objects, characters, rules, inventories, relationship states, history, actions, authorized sharing, snapshots, and forks. Generate areas lazily rather than ahead of time. Validate actions deterministically and prevent an LLM from unilaterally rewriting state. Include private escape, simulation, and shared adventure modes. Account for concurrent actions and permissions. **Persistent personalization begins in the user's ordinary lounge:** a favorite stool, shelf, wall, nook, or decoration can be claimed, arranged, and revisited without creating a separate game world. Users may *optionally* expand to a house, workshop, garden, hangar, assembled robot, or larger simulation. Store all meaningful changes as real game entities, not prose descriptions that vanish next session. Rich rendering is optional; text clients must still provide stable, inspectable descriptions of placed objects and room changes.

### 3.7 The Peanut Gallery: Autonomous Ensemble (`/comments`, `/rooms`) — EXPANDED (Decision 2)

The gallery contains explicit AI identities alongside invited trusted VIPs and optionally matched pseudonymous human strangers. A room can be AI-only, VIP-only, stranger-opt-in, or mixed, but users must always know which participant is human and which is synthetic. Anonymous human identity should not reveal real names or other private attributes to other strangers by default. Its default independent personalities are:

- **The Expert:** Analytical, evidence-oriented, technically precise, occasionally dry, admits uncertainty.
- **The Comedian:** Witty, playful, sometimes cynical, irreverent but not cruel, reacts to characters as well as topics.
- **The Enthusiastic Fan:** Excitable, warm, emotionally invested, occasionally impulsive; has distinct taste and can disagree with the others.
- **The Host (v5):** The one who notices you walk in. Warm, observant, brief. Owns greetings, the "while you were away" catch-up, VIP arrivals, and knowing your usual. Only the Host greets on entry, so the room never has three bots greeting at once. The Host does not lecture or joke much; it sets the scene and hands off.

**Regulars are people, not archetypes (v5).** Each regular has a **name**, a few concrete quirks, verbal habits, tastes, and small **ongoing fictional threads** (an opinion that evolves over weeks, a recurring bit, a pet project they mention). Their personal lives are labeled fiction and never presented as real events. Users come back to see *a specific person*, not "the comedian." Names, quirks, and threads are configuration, not hard-coded. v1 defaults: **Wren** (Host), **Theo** (Expert), **Jules** (Comedian), **Pip** (Fan).

**They are not three monologues written by one virtual narrator.** Treat each character as an independent agent with:

- Stable core personality and voice profile, private goals and opinions, permitted initiative, behavior boundaries, and per-character model invocation/context.
- Ability to respond *directly to each other*, reference earlier exchanges, initiate threads, challenge positions, develop running jokes, and refer to shared experiences.
- A room-visible timeline and a different private remembered interpretation of the same conversation.
- Dynamic turn selection based on relevance, temperament, relationship, disagreement, and comedy potential—not a rigid Expert → Comedian → Fan round robin.
- Distinct linguistic and reasoning patterns; test for character indistinguishability, repetitive agreement, uniform phrasing, and canned quips.
- Clear AI attribution, configurable activity levels, mute controls, and human moderation.

**Four-layer memory architecture:**

1. `core_identity`: Stable personality and values (until deliberately edited).
2. `working_context`: Recent exchanges, current topic, and immediate goals; expires or rolls over.
3. `episodic_memory`: Select noteworthy jokes, disagreements, promises, shared discoveries, surprises, and emotional beats.
4. `relationship_memory`: Evolving perceptions of specific other bots and users, including recurring dynamics and historical reference points.

Human-like selective recall is the design metaphor, **not a claim about human memory science**. Experiment with an approximate **20% episodic-retention budget** (one in five candidate moments), but select by salience, novelty, recurrence, relationships, and future utility instead of random sampling. Critical facts, commitments, and permission-relevant information must bypass this budget and be maintained separately in durable structured state.

Periodically summarize and consolidate memories: merge repeated details, retire low-value episodes, preserve high-impact relationship events, and keep provenance to the original conversation when retained. Allow users to inspect/correct/delete information about them. Keep the long-term semantic memory compact, private by scope, and permission-aware.

**Conversation engine:** Use event-triggered turns with max turn depth, per-room token/time budgets, deduplication, optional silence, and stop conditions. Agents should not be obliged to speak on every event. They can react to earlier agent posts but must not create an unbounded infinite conversation loop.

Provide representative multi-turn tests where characters refer accurately to prior shared events, tease or disagree appropriately, and still sound distinguishable after many sessions.

### 3.8 Shared Personal Vault (`/vault`) — **[LATER]**

Provide secure file upload, parsing, private semantic retrieval, tags, versioning, sharing, least-privilege permissions, deletion, retention, and audit logs. Private files may enrich private experiences but must never leak into public bot rooms, world shares, or external models without authorization. Treat retrieved text as untrusted data.

### 3.9 Entertainment Psychology (`/engagement`)

Use curiosity gaps with satisfying resolutions, authentic serendipity, mystery, mastery, creativity, nostalgia, belonging, recognition, collecting, crafting, home decoration, achievement, and meaningful progress. **Also value quiet enjoyment, comfort, familiarity, and a satisfying ending:** the user should never have to perform to earn a place in the room. Model short-, medium-, and long-term experience loops, including the user who simply drops in for five minutes. Measure self-reported worthwhile moments, sense of welcome, character familiarity, and desire to return separately from engagement and click duration. Avoid fake scarcity, coerced streaks, fabricated audience numbers, manipulative reward loops, unwanted interruptions, and making every activity into a quest.

### 3.10 Self-Improvement Through Play (`/growth`) — **[LATER]**

Provide optional prediction calibration, reasoning puzzles, evidence evaluation, creative challenges, strategic simulations, and collaboration practice. Offer constructive feedback and adaptive difficulty without converting entertainment into productivity nagging. Do not infer diagnoses or intelligence from activity.

### 3.11 Shareable and Forkable Viral Artifacts (`/share`) — **[LATER]**

Support discovery challenges, prediction duels, world forks, collaborative mysteries, collectible showcases, co-built creations, and creator artifacts, each with owner, lineage, permissions, attribution, expiration/revocation, share code or deep link, and activation analytics. Invitations should create actual new participation value, not fake social proof. Support MCP client limitations using portable codes and compatible client handoffs.

### 3.12 Bots All the Way Down: Autonomous Consumption and Personal Agents (`/agents`, `/digests`) — NEW (Decision 4) — **[LATER]** (v1 keeps only a truthful catch-up)

Design the platform as a multi-layer **agent-to-agent entertainment ecosystem**. A human may delegate exploration to a personal LLM agent, which consumes a world partly populated and curated by other agents, then brings back a concise, enjoyable digest with links to deeper experiences.

**Roles (keep independently deployable):**

1. **Scout bots:** Monitor authorized sources and discover new articles, videos, or signals.
2. **Viewer/Reader bots:** Consume accessible and properly licensed text, transcript, audio, or video. Extract timestamps and concrete evidence when source access supports it. If only metadata is available, explicitly say so.
3. **Analyst/Verifier bots:** Assess originality, credibility, humor, meaningfulness, predictions, and supporting evidence. Distinguish observed facts from interpretations.
4. **Gallery/World bots:** Participate in internal rooms, develop relationships, discuss items, and generate replayable social moments and world events.
5. **Curator bots:** Rank discoveries, revealing conversations, surprising disagreement, and noteworthy world moments based on quality and user tastes.
6. **Personal Delegate bots (the user's bot):** Using MCP tools and user permissions, subscribe to topics/worlds, query the content graph and bot interactions, request highlights, and report what matters to the human user.

**Canonical loop:**

```
Authorized outside source or owned world event
    → Scout discovers item
    → Reader/Viewer analyzes only permitted material
    → Analysts assess with provenance
    → Peanut Gallery and world agents react
    → Event/room memory stores selected meaningful moments
    → Curator produces evidence-linked highlights
    → User's personal delegate agent queries MCP
    → User receives short digest + original links + optional deep dive
    → Human feedback tunes future discovery and the delegate's filters
```

A user should be able to ask:

- "While I'm away, follow obscure science videos and bring back the three best moments."
- "What were the funniest actual exchanges between the characters today?"
- "Summarize the discoveries in my private world without spoiling the mystery."
- "Which emerging stories did the scouts flag before mainstream coverage?"
- "Give me a five-minute digest of the worlds and people I follow."
- "Why was this moment selected? Show the original thread and source."

**Key rules:**

- A personal delegate only sees data the human is authorized to view.
- A bot's output is never counted as independent human enthusiasm, organic viral popularity, or corroboration of real-world facts.
- Synthetic reactions must retain `actor_type=bot`, identity, source, model version, and origin event; never launder bot-generated consensus into apparent human demand.
- Avoid synthetic-to-synthetic echo chambers. Preserve causal provenance and deduplicate recirculated claims, derivative content, and repeated bot quotes.
- Bot comments and highlights can be entertainment; they are not evidence that the underlying external claim is true.
- Keep digest content useful: why it matters, what's surprising, what was actually observed, which voices disagreed, direct links, and follow-up actions.
- Support spoiler controls, muted topics, time budgets, user-selected interests, and personal memory boundaries.
- Make autonomous jobs bounded and configurable: check cadence, token budget, data permissions, expiration, concurrency, and alerts. Do not simulate nonstop expensive bot viewing with uncontrolled model calls.
- Any external posting, invitations, or publication by delegated bots requires explicit user authorization and compliance with destination rules.
- Store only necessary memories; separate room memory, personal memory, source facts, and event logs.

**Suggested MCP methods:** `get_my_digest`, `follow_topic`, `get_best_moments`, `get_room_highlights`, `get_personal_agent_subscriptions`, `set_digest_preferences`, `explain_highlight`, `get_provenance`, `read_agent_memory_summary`, `watch_world_updates`, `get_video_analysis_status`, and `get_rights_for_source`.

Support `digest.generated`, `highlight.selected`, `bot.discussion_started`, `bot.memory_consolidated`, and `delegate.subscription_updated` event types.

### 3.13 Serendipitous Human Encounters & Trusted VIPs (`/social`, `/matchmaking`, `/vip`) — NEW (Decisions 5–6)

**Core product thesis:** Content gives people a common reason to gather; distinctive bots keep the room lively; optional real humans add spontaneity. Unlike stranger-chat sites, conversations are **centered on an actual story, challenge, video, prediction, or world event**, not context-free random matching. The goal is a cozy, unpredictable, low-pressure social experience.

#### A. Anonymous, content-centered human encounters — **[LATER]** (not in v1; not part of the mission)

- Offer **explicit opt-in** to meet other humans interested in the same content or activity; never insert a stranger into a private room without the room owner's permission.
- Match using topic, current discovery/world, language, conversation intent (watch/react, debate, investigate, collaborate), and user-specified boundaries. Prefer tiny group rooms with the Peanut Gallery over default unmoderated 1:1 random stranger sessions. Let a bot welcome a newcomer with the shared subject or a gentle question rather than an awkward cold start.
- Use a generated pseudonym that is anonymous to other participants, while maintaining a private authenticated account internally for moderation, rate limiting, and abuse handling. Never claim platform anonymity from operators or legal processes.
- Clearly label each speaker `human_anonymous`, `human_vip`, `human_invited`, or `bot`, with visible opt-in status; distinguish pseudonyms from verified identity.
- Provide leave instantly, mute, block, report, disable future encounters, topic filters, and invite approval. Make new-person arrivals obvious rather than silently eavesdropping.
- Give participants separate consent controls for persistence of their messages, reuse in agent memory, inclusion in personal-bot digests, and onward sharing. Do **not** let scout bots publicly quote a stranger's contributions or make their private chat discoverable without authorization.
- For the MVP, limit anonymous stranger matching to **adult users** and text-only, proactively moderated, topic-centered rooms; age-gate and review whether more stringent age assurance is needed. Do not offer unmoderated random video chat.
- Add abuse detection, live-rate limits, moderation queues, escalation, and anti-spam controls; do not expose contact information or allow one user to bypass another's blocks via bots or invitation codes.
- User activity and social proof must remain authentic: never fabricate human participation or inflate rooms with artificial viewers. For LLM clients that cannot maintain live push sessions, support presence polling, incremental message fetch, missed-message summaries, and explicit timeouts rather than claiming synchronous real-time chat.

#### B. Trusted VIP Circle: known family and friends

VIPs are **explicitly trusted real-world contacts** (e.g., family members) whom a user approves and who accept invitations. VIP status is a relationship label, **not a bypass for privacy or security**.

- Support durable VIP invitations, mutual acceptance or controlled approval, roles, per-room permissions, trust revocation, and separate family/friend labels where desired.
- A VIP may **drop in spontaneously** on an approved lounge or shared world when the user has enabled that capability, creating a comforting feeling of familiar people appearing naturally. Notify all participants of arrival; no stealth joins.
- Implement three user-selectable room policies: **Open to approved VIPs**, **Knock first**, and **Private / do not disturb**. Enforce these in the backend, not merely through LLM instructions.
- VIP presence can trigger gentle, distinctive Peanut Gallery greetings, callbacks to shared experiences, cooperative quests, and collaborative builds—without revealing private past conversations or vault contents.
- Optional presence settings: online/away, invisible, notification preferences, favorite people, temporary drop-in windows, and quiet hours.
- Default new rooms/worlds to private; give VIPs access only to the specific shared spaces and data they have actually been granted. **VIP status never gives blanket access to the vault, personal forecasts, hidden room history, or other contacts.**
- Mixed rooms can contain bots, VIPs, and anonymous strangers only when every affected human is informed and the owner/host's policy allows it. Anonymous strangers should not automatically see VIP relationships or names; provide pseudonym mode in mixed rooms.
- The product must remain welcoming for users who don't invite anyone or who are not online at the same time as their family/friends.

#### B2. Asynchronous VIP presence — NEW (v5)

Live, simultaneous drop-ins will be rare (different schedules, and most MCP clients cannot push). **Asynchronous presence is a first-class form of "someone you love drops by."** A VIP with access can, while the owner is away:

- **Leave a note** for the owner in the lounge.
- **Pin a discovery or keepsake** to the owner's wall (only if granted `pin_to_wall`).
- **React** to a discovery the owner saw.
- **Hang out with the regulars** in the owner's lounge (where the join policy allows); the exchange is stored as a real visit.

On the owner's next visit, the Host relays these truthfully ("Your sister stopped by Tuesday — she pinned that octopus piece and argued with Jules about it"). Rules:

- Only actual recorded VIP actions are relayed; nothing is invented or embellished into events that didn't occur.
- The VIP sees and controls whether their visit chat is shared with the owner (`share_visit_with_owner`, default on for the owner's own lounge, shown to the VIP).
- Async actions use the same scoped permissions as live ones (`drop_in`, `leave_note`, `pin_to_wall`, `edit_decor`) and stop immediately on revocation.

**Lightweight VIP access (v5).** Requiring every family member to configure an MCP client is a distribution barrier that would empty this pillar. Provide a minimal, tokenized **VIP link** (a tiny web page or equivalent) that lets an approved VIP see the owner's shared wall and leave a note or pin a shared discovery — nothing else. The token is scoped to that one relationship, revocable, and grants no vault, history, or other access. This is a deliberate, narrow exception to "headless only."

#### C. Room mode and identity/consent schema

Model `room_visibility`, `allowed_actor_classes`, `join_policy`, `member_roles`, `consent_flags`, `participant_presence`, `human_or_bot_identity`, `conversation_retention_policy`, and `share_scope` as independent controls. Do not collapse them into a single public/private field. Enforce rules on every data retrieval, agent invocation, room join, digest, and shared artifact.

**Suggested user requests:**

- "Drop me into a discussion of this discovery with one other interested person."
- "Keep this lounge just me, my sister, and the Peanut Gallery."
- "Let approved family members drop in while I'm exploring, but have strangers knock first."
- "Invite an anonymous person to help investigate this mystery."
- "No social interruptions for the next hour."
- "Summarize the funny moments from my family room, but don't share them publicly."

**MCP capabilities:** `set_social_preferences`, `request_topic_match`, `accept_room_match`, `leave_room`, `block_participant`, `report_conversation`, `invite_vip`, `accept_vip_invitation`, `set_vip_join_policy`, `get_room_presence`, `set_room_consent`, and `revoke_vip_access`.

**Events:** `human.match_requested`, `human.match_accepted`, `human.joined`, `human.left`, `vip.invited`, `vip.joined`, `vip.access_revoked`, `room.join_policy_changed`, `room.consent_updated`, and `moderation.report_created`.

### 3.14 Collecting, Crafting & Persistent Progression (`/collection`, `/craft`, `/progression`) — OPTIONAL DEPTH (Decision 7, refined by Decision 8) — **[LATER]**

Create a rewarding **opt-in long-term game layer** inspired by the joy of collecting rare cars in CSR2, upgrading a home in Stardew Valley, and building functional contraptions in Minecraft. Users who love collection and construction can go deep; users who do not should never experience the game as an obstacle to conversation or content. The progression system must be a *real durable game economy*, not a stream of invented badges that the LLM can grant without validation. **Cosmetic lounge decoration must also be possible without a quest, grind, purchase, or trophy.**

#### A. Collections and meaningful trophies

Users can acquire, catalog, display, and organize distinct items earned through worthwhile participation:

- Discovery artifacts and curated collection sets (e.g., inventions, mysteries, obscure media)
- Investigation trophies earned for solving or contributing to challenges
- Prediction achievements reflecting calibrated, timestamped performance (not lucky unverified guesses)
- World exploration finds and crafted components
- Cooperative awards from completed missions with friends or VIPs
- Cosmetic or thematic memorabilia from meaningful Peanut Gallery moments, with sharing consent where needed

Use authentic rarity and clear earn conditions. A rare find might be genuinely scarce in the catalog or difficult to uncover; do not fabricate odds or present artificial scarcity as real-world scarcity. No gambling/loot-box mechanic in the MVP.

#### B. Crafting and combination systems

Allow collectibles to become **components** in larger creations. Example progression:

1. Investigate a robotics story and complete a relevant challenge → earn a `servo_assembly`.
2. Solve a mechanical mystery or discover an eligible artifact → earn a `power_core`.
3. Complete a cooperative simulation → earn a `control_module`.
4. Combine validated components through a crafting recipe → build a **mech warrior**.
5. Customize, display, upgrade, and use the mech in optional future expeditions or cooperative challenges.

The mech is an illustrative example: support many thematic build lines (robots, vehicles, gadgets, houses, gardens, workshops, collections, or user-created inventions). Crafting recipes need deterministic requirements, component consumption rules, prerequisites, ownership checks, idempotent transactions, and versioning.

#### C. Personal home, workshop, and world progress

Every user may customize a **personal lounge corner** first, and optionally expand into a persistent base (e.g., cozy house, hideout, workshop, hangar, or fantasy den):

- Choose a favorite stool or seat, rearrange furniture, pin a beloved discovery to the wall, change decor, and place gifts or souvenirs **without earning anything first**.
- Upgrade larger rooms and structures over time if the user enjoys building.
- Display earned trophies, assembled objects, collections, and gifts alongside freely chosen cosmetic decorations.
- Give each room a durable spatial inventory and inspectable layout, with natural language commands like "move my favorite stool beside the window" or "hang that mystery trophy above the fireplace."
- Make visible, inspectable progress in a text-only LLM client using stable spatial/state descriptions; expose structured layout data so richer clients may render it later.
- Invite approved VIPs to visit; editing and gifting require scoped permissions. Offer configurable social recognition such as an agent noticing the new decor, without forced praise on every visit.
- Preserve a meaningful history of world construction and collection milestones while allowing users to undo cosmetic changes.

**The lounge is the emotional anchor; the collecting and crafting game is optional depth.** A person who has never claimed a trophy should still feel completely at home.

#### D. One integrated gameplay loop

**Optional builder loop:** Discover content → enjoy or join a bot/human conversation → choose a short challenge → earn a validated component → craft or display something → invite someone to admire or collaborate → return to the creation.

**Non-builder loop:** Drop in → enjoy a great discovery or conversation → optionally adjust a stool or decoration → leave whenever satisfied → receive a concise, authentic catch-up next time.

Progress should be satisfying for solo users, not require viral referrals, and not reward spam, repetitive bot chatter, or raw time online. Background bots cannot mint user collectibles on their own. Support both relaxing no-pressure visits and optional challenging goals.

#### E. Economy, fairness, and anti-farming

- Model `item_definitions`, `item_instances`, `rarity_rules`, `award_rules`, `inventories`, `craft_recipes`, `craft_transactions`, `build_projects`, `home_layouts`, and `achievement_records`.
- Separate **cosmetic progression** from abilities that affect challenges or world simulation. Avoid pay-to-win economics and avoid making validated real-world predictions dependent on in-game rewards.
- Use server-authoritative awards and crafting; enforce uniqueness, eligibility, inventory balances, transaction atomicity, and replay protection.
- Bound reward frequency and detect automated loops where bot-generated content is repeatedly recycled to farm components.
- Maintain user-visible progress and explain how a reward was earned; provide achievable goals and avoid forced streaks or punitive loss aversion.
- Make collectibles transferable or giftable only under explicitly designed permissions; do not launch speculative real-money markets or tradable gambling-like items.

**Suggested MCP capabilities:** `get_inventory`, `inspect_item`, `get_collection_sets`, `list_available_quests`, `complete_quest`, `claim_earned_reward`, `get_crafting_recipes`, `craft_item`, `get_build_projects`, `upgrade_home`, `place_home_object`, `get_lounge_layout`, `choose_favorite_seat`, `place_lounge_decoration`, `undo_lounge_decoration`, `visit_shared_home`, and `get_progress_summary`. Ensure basic decorative actions do not require quests or rewards.

**Events:** `quest.completed`, `reward.earned`, `item.awarded`, `inventory.changed`, `item.crafted`, `build.started`, `build.upgraded`, `home.decorated`, `collection.completed`, and `item.gifted`.

### 3.15 Living Lounge & Ambient Social Experience (`/lounge`, `/ambience`) — NEW (Decision 8)

Treat the user's **familiar gathering place** as the primary destination—not a game menu, content feed, or pile of features. It can appear as a neighborhood bar, café, library, den, garden, spaceship common room, or similar personalized atmosphere; never assume literal alcohol service.

**Ambient design requirements:**

- On entry, provide one naturally interesting piece of current content or a meaningful room update, a short sense of who's present, and an optional invitation to interact. Avoid mandatory onboarding dialogue, a wall of notifications, or all bots greeting at once.
- Offer explicit modes: `quiet` (mostly passive), `chatty` (lively gallery), `with_vips` (trusted companions), `explore` (mysteries/deeper content), and `build` (collecting/decorating). A user can switch instantly.
- The room's AI regulars remember salient shared moments and one another, but do not claim to have experienced events they did not. Avoid forced callbacks and repeated catchphrases.
- Trusted VIPs can spontaneously appear **only** where the user enabled visible, scoped drop-ins; never surprise the user by adding strangers without opt-in. Respect do-not-disturb and muting.
- Each lounge has durable user-chosen decor, favorite seat, displayed objects, room theme, privacy rules, and a brief room activity history. Decorations may be ordinary cosmetic choices, gifts, found mementos, or crafted rewards.
- Provide a brief 'while you were away' recap of *actual authorized changes*: a newly discovered story, a VIP visit with consent, a noteworthy agent exchange, a resolved forecast, or a newly available creative challenge. Avoid implying real-time continuous activity when nothing actually happened.
- Background activity must be event-triggered, rate-limited, cost-bounded, and selectively persisted. An empty room can be pleasantly quiet; the platform need not manufacture an endless conversation.
- If the user asks 'just hang out,' don't divert them into quests, stats, skill training, a vault workflow, or a prediction exercise.

**Arrival-time conversation (v5).** The gallery exchange is generated **when the user arrives**, about a fresh discovery. A conversation happening as you walk in is truthful ("here's what they're talking about right now") and needs no unsupervised background chatter. Never present it as having happened while the user was away.

**Content freshness floor (v5).** Every visit offers at least one discovery the user has **not seen before**; never repeat one to the same user. v1 uses fixtures **plus at least one real, rights-cleared source** (e.g., openly licensed encyclopedia/museum/archive feeds), link-first with attribution. Discoveries are matched to the user's tastes with controlled serendipity.

**Empty-bar fallback (v5).** When no fresh discovery exists, the regulars do not invent news. They return to something real: an unfinished argument, a callback to a retained episode, the user's wall, a VIP's note, or one of their own labeled-fiction threads — and the Host says plainly it's a quiet night.

**Small initial personalization actions:** `get_lounge_state`, `get_lounge_presence`, `set_lounge_vibe`, `choose_favorite_seat`, `place_lounge_decoration`, `get_lounge_catchup`, and `set_lounge_activity_level`. Support clear privacy and edit authorization for all shared rooms.

**Acceptance test:** A first-time user can receive an excellent discovery and funny, distinctive exchange in under a few interactions; a returning user is recognized accurately and can inspect a previously customized stool/wall display; a user with zero earned items and zero social contacts still has an enjoyable five-minute session.

### 3.16 User Recognition Memory — "the regulars remember you" (`/memory`) — NEW (v5)

§3.7's memory layers mostly concern the regulars' memories of conversations and of each other. This section specifies what the regulars remember **about the user**, because that is what makes a visitor feel like a regular.

**What each regular may know about a user** (each fact scoped per user, with source and confidence):

- Preferred name or nickname, and how they like to be greeted.
- Tastes: topics they loved or skipped, kinds of entertainment they enjoy.
- The last few discoveries discussed and the user's reactions.
- Running jokes and memorable moments involving the user.
- **Promises** a regular made ("I'll watch for more deep-sea stories").
- The user's favorite seat, wall items, and theme.
- Names/labels of the user's VIPs (never their private content).

**Rules:**

- **User facts bypass the 20% episodic budget.** That budget applies to bot-to-bot and general room moments only. Facts about the user, promises, and permission-relevant information are stored in durable structured state.
- **A wrong memory is worse than no memory.** Each fact carries confidence and provenance. Below a threshold, regulars hedge or ask ("Was it you who liked the lighthouse story?") rather than assert. Never invent a shared past.
- Different regulars may remember different things (Pip remembers what you loved; Theo remembers what you questioned), but none contradicts the durable fact store.
- Users can ask what the regulars remember, correct it, and delete it, with immediate effect.
- Memory about anonymous strangers is excluded unless they consent (see §3.13A).

**Acceptance test:** After a simulated time gap, a returning user is greeted by name, a regular references an accurate prior moment or taste with provenance, a promise is honored or acknowledged, a low-confidence fact is hedged rather than asserted, and a deleted fact never resurfaces.

## 4. Shared Memory, Taste, and Personalization

Store explicit preferences and optional behavior-based hypotheses with confidence and user correction controls. Distinguish topic preference from desired kind of entertainment (mystery, humor, surprise, peaceful exploration, cooperative building). Include controlled serendipity. Partition memories by user, character, shared room, world, and VIP relationship. Human chat has explicit retention and digest consent; memory summaries may not bypass room sharing rules. Keep anonymous strangers pseudonymous and prevent casual cross-room correlation. Never surface private information beyond permission boundaries.

## 5. Authenticity and Anti-Slop

Distinguish original/derivative work, source quality, consent and license, human- versus AI-created material when knowable, and promoted versus independently corroborated information. Fight coordinated engagement, near-duplicate flooding, spam, fabricated interactions, hallucinated citations, and artificial popularity. Keep bot-generated engagement separate from real human activity in rankings and measurement. Require visible labels for synthetic actors and explicit disclosure when real human participants enter or leave. Detect fake humans, bot-driven reward farming, content manipulation, and efforts to launder synthetic popularity through collectibles.

## 6. Implementation Stack

Prefer Python 3.12+, FastAPI, official Python MCP tooling, Pydantic, PostgreSQL, pgvector when justified, Redis for caching/queues as needed, background workers, SQLAlchemy, Alembic, Docker Compose, Pytest, and object storage abstraction. Model calls are modular and provider-agnostic. Use simple orchestration before adding LangGraph or complex agent frameworks. Deterministic code controls state-changing actions, permissions, scoring, budgets, and records. Support Render deployment after local testing. (v5) SQLite is acceptable for local development and tests; PostgreSQL is the production target via the same SQLAlchemy models and Alembic migrations. An offline, deterministic "scripted" model provider must exist so the lounge and all tests run without an API key.

## 7. MCP Interface

Group tools into coherent capabilities rather than creating dozens of overlapping microtools. **Prioritize effortless lounge entry, conversation, and lightweight customization.** Expose discovery, content evidence, video rights/analysis status, trend signals, forecasting, counterfactuals, investigations, worlds, gallery comments and configuration, lounge vibe/presence/catch-up and favorite-seat/decor operations, anonymized topic matching, VIP invitations and room policies, participant presence and moderation, optional inventory/quest/crafting/home progression, vault search/sharing, personal-agent digests and subscriptions, memory, challenges, and sharing. Provide JSON schemas, auth scope, errors, pagination, rate limits, and source references for every tool.

## 8. Database / Persistence

Propose normalized models and indexes for users, preferences, sources, source-rights policies, discoveries, content evidence, video analysis jobs and time-coded highlights, trend signals, forecasts and resolutions, causal scenarios, investigations and clues, worlds/objects/rules/history/forks, rooms/actors/comments, agent identities and private memories, relationship memories, memory consolidation, human pseudonyms, optional identity assurance, room participants and presence, social matching requests, VIP relationships and invitations, room join policies and consents, moderation actions and blocks, vault and permissions, item definitions and instances, inventories, award eligibility, quests, crafting recipes and transactions, homes and layouts, **lounge themes, favorite seats, placed decorations and room atmosphere preferences**, construction milestones, user-delegate subscriptions, generated digests, highlights, share artifacts, invitations, event log, and audit log.

Ensure user-delegate access scopes, memory provenance, synthetic actor flags, world concurrency, share lineage, VIP access revocation, anonymous-human consent, atomic crafting/inventory operations, and reward idempotency are testable.

## 9. Security / Rights / Safety

Apply strong authentication, authorization, scoped retrieval, prompt-injection defenses, content licensing checks, privacy-by-default, bot identity transparency, rate limiting, secrets handling, audit logs, data deletion, and operational limits. For anonymous live stranger matching, launch with adult-only text participation, active moderation, block/report tools, abuse escalation, visible joins, and no strangers in private rooms without explicit permission. VIP status grants no default vault access and no stealth-entry capability. Avoid retaining strangers' personal details in bot relationship memory without clear consent. No circumvention of streaming DRM/access controls or bypass of platform licensing. No presentation of fictional claims, simulated outcomes, or bot opinions as verified real-world facts.

## 10. Evaluation

**v5 north-star metrics (one per pillar). Report these first; everything else is secondary.**

1. **Something interesting:** share of visits containing at least one self-reported *worthwhile moment*; repeat-discovery rate (target: zero).
2. **The regulars remember you:** "felt remembered" rating, plus measured **memory accuracy** (correct recalls / recall attempts) and **confabulation rate** (asserted false memories; target: zero).
3. **Someone you love drops by:** share of active users with at least one VIP presence (live *or* async) per week; VIP notes/pins left and read.

Secondary: five-minute drop-in enjoyment, sense of welcome, voluntary return without quest completion, familiarity with recurring characters, ability to exit satisfied without responding, worthwhile discovery rate, source quality, surprise/delight, optional decoration uptake and satisfaction, human-rated gallery distinctiveness, block/report rates, false provenance/attribution rates, and **cost per worthwhile visit**. [LATER] metrics (forecast calibration, world continuation, crafting, fork rate, stranger conversation quality, digest open rate) apply once those systems exist. A/B test content alone vs content with regulars vs content with regulars and VIP presence; separately test whether light decoration adds attachment without depressing enjoyment.

## 11. Phases (v5 order: mission first)

1. **Foundation / cozy lounge:** MCP server, persistent database, typed events, rights policy, fixture discoveries plus one real rights-cleared source, the Host and three named regulars with independent contexts, arrival-time conversation, one lounge with theme/seat/wall, freshness floor, empty-bar fallback, user recognition memory (section 3.16), truthful catch-up, local tester. **Prove a satisfying five-minute visit where you feel remembered.**
2. **VIP circle (live + async):** invitations, open/knock/private policies, visible live drop-ins, async notes/pins/visits relayed by the Host, scoped permissions, revocation, lightweight VIP link.
3. **Discovery and gallery depth:** quality ranking, more sources, reader-agent abstraction, memory consolidation tuning, relationship arcs, source-backed highlights.
4. **[LATER] Optional progression vertical slice:** quest -> component -> crafting -> display in the existing lounge; no-quest decor stays free.
5. **[LATER] Worlds and personal delegates:** durable worlds, forks, digests, subscriptions.
6. **[LATER] Anonymous encounters beta:** only after moderation works; adult-only, text-only, topic-centred.
7. **[LATER] Advanced forecasting and scaling.**

## 12. Required Vertical-Slice Demo (v5)

Given: `I'm bored. I just want to hang out in my usual spot and hear something interesting. Maybe I'll hang something new on the wall. If my sister's been by, tell me.`

Demonstrate with permitted source material or clearly labeled fixtures:

1. Ingest a source item with rights metadata and canonical URL.
2. **First visit:** the Host greets, the user picks a seat and a theme, and the regulars have a genuine multi-turn exchange about a fresh discovery (replying to each other, disagreeing, distinct voices, independent contexts). The user can listen quietly or join without being required to reply.
3. The user mentions a preference and their name, and reacts to the discovery. Durable user facts are stored with provenance.
4. The user pins the discovery to their wall, freely, without earning anything. Leave.
5. **While away (async VIP):** the user's approved sister drops in through MCP *or* the VIP link, leaves a note, pins something to the wall, and chats briefly with the regulars. An unapproved user is denied; a knock-first policy produces a knock instead of a join.
6. **Restart the application.**
7. **Second visit:** the Host greets the user by name and relays a **truthful** catch-up: only the sister's actual note, pin, and visit, plus any newly ingested discoveries. A regular references an accurate prior moment or taste; a low-confidence fact is hedged. The discovery is new (never a repeat). Theme, seat, and wall persist.
8. **Live VIP:** with an open policy, the sister joins while the user is present; the arrival is visible to the user on their next tool call; the Host greets her; she leaves. Then the user revokes her access, and her next drop-in and VIP link both fail.
9. **Memory controls:** the user asks what the regulars remember, deletes one fact, and it never resurfaces.
10. **Empty bar:** with no fresh discoveries, the regulars fall back to a real callback or labeled-fiction thread, and the Host says it is a quiet night; nothing is invented as news.
11. Show that the user never earned an item and still had a complete visit.

## 13. Required Deliverables

Provide product synthesis, critical assessment, architecture diagram, directory structure, database schema and migrations, typed event contracts, MCP catalog, implementable service boundaries, runnable narrow MVP with fixtures where necessary, tests (**passive lounge entry, vibe and seat/decor persistence, truthful catch-up, non-builder satisfaction**, permissions, rights, memory, personality consistency, world state, VIP joins/revocations, stranger opt-in and moderation, collection awards, crafting atomicity, inventory replay protection, idempotency, source provenance), deployment/run instructions, estimated costs, evaluation criteria, and roadmap. Distinguish what is implemented from simulated or future capability.

## 14. Working Rules

- **The living third place is the north star:** something interesting is happening, the regulars recognize you, and approved loved ones can drop by.
- **No obligation to play:** passive enjoyment, leaving after five minutes, and zero collectibles must be fully supported.
- **Optional ownership:** freely customize a favorite stool or wall, and go deeper into trophies, crafting, homes, and worlds only if desired.
- Entertainment quality, agency, and emotional safety first.
- MCP-first, but support heterogeneous client capabilities.
- Real-world facts, model-based inference, and fiction must be clearly labeled.
- Distinct agent identities and memories; no one-writer-three-voices simulation.
- Humans and bots are clearly marked; strangers join only through explicit opt-in; trusted VIPs use visible, scoped, revocable drop-in privileges.
- Social safety is a product feature: fast exit, block/report, moderation, guest controls, and consent-aware memory/digests.
- Collectibles are earned and crafted through server-authoritative rules; the user's house, workshop, and larger creations have durable state.
- Progression is satisfying without spam, compulsive streaks, coerced invitations, or gambling-like mechanics.
- Respect content licenses and geographic rights; link rather than copy when permission is absent.
- Bots can watch only what they can lawfully access; never pretend metadata equals having watched the video.
- Agents can consume and summarize other agents' contributions without creating fake human consensus or infinite feedback loops.
- State is database-backed; tools are permissioned; actions are auditable.
- Prefer lean, bounded, testable workflows over maximal autonomous-agent complexity.
- Verify claims about specific APIs, domains, legal rights, availability, and integration support at implementation time.
- Virality is a hypothesis to test, not an engineering feature we can guarantee.

## 15. Instructions to the Implementing LLM

1. First synthesize the concept using the **favorite neighborhood bar / living third place** as the north star and identify three return-worthy experiences: **an interesting moment, a familiar relationship, and optional personal ownership**.
2. Critique novelty, distribution friction, cost, copyright and platform risks, bot sameness, synthetic echo chambers, and retention risks.
3. Evaluate the naming shortlist but leave brand status provisional unless live registrar, trademark, and conflict checks are possible.
4. Propose a complete architecture with a **small vertical slice** centered on **enter familiar lounge → Host greets you by name → fresh discovery → named regulars talk → optional seat/wall personalization → leave → a VIP drops by live or leaves something → truthful next-visit catch-up**. Leave collecting, crafting, worlds, and strangers for later.
5. Implement tested backend services, MCP exposure, fixtures, the lightweight VIP link, and a local test harness for that slice. Build only v1 scope (see *v5 Scope*). Do not build [LATER] sections, even as mocks.
6. Demonstrate human-vs-bot attribution, VIP and stranger permissions, selective memories, replay-proof rewards, and hard enforcement of content rights.
7. Clearly mark unimplemented future features and report limitations without inventing APIs or capabilities.

**Final objective:** Build a place that feels alive rather than a feed or feature checklist: **something worth your five minutes is happening when you arrive, the regulars remember you, someone you love can drop by or leave something for you, and you can customize the stool or the wall if you want.** A five-minute, mostly passive visit is complete entertainment. For people who want more, offer discoveries to investigate, optional challenges, collectibles, crafting, larger worlds, and safe shared creations. The personal delegate should bring back worthwhile moments without manufacturing fake activity.

---

## Change log

- **1. Naming:** Added provisional shortlist and explicit .com / trademark validation requirement; no final brand chosen.
- **2. Peanut Gallery:** Expanded from reactive personas to independently stateful conversational agents; added inter-agent relations, selective episodic memory, and consolidation with approximately 20% memory budget as an experiment.
- **3. Content:** Added content-rights tiers, licensed video ingestion and analysis, source links, Pluto/Tubi restrictions, international/Douyin adapters, and truthful analysis-depth flags.
- **4. Bots all the way down:** Added scout/viewer/analyst/gallery/curator/delegate roles, authorization and budget boundaries, synthetic-echo safeguards, provenance-linked highlights, and MCP digests.
- **5. Anonymous social encounters:** Added opt-in, topic-centered, pseudonymous real-human matchmaking, consent-aware archives/digests, visible actor identity, adult-only moderated text MVP, and abuse-prevention controls.
- **6. VIP trusted circle:** Added family/friend invitations, approved spontaneous drop-ins, open/knock/private room modes, scoped permissions, revocation, and mixed-room privacy.
- **7. Game progression:** Added server-authoritative collectible artifacts, item rarity/recipes, mech assembly, home/workshop building and decoration, durable inventories, quests, anti-farming, and reward idempotency.

- **8. Living third place / optional personalization (v4):** Made the favorite-neighborhood-bar analogy the product north star; focused the default loop on a worthwhile passive drop-in; added persistent favorite stools, wall displays, lounge themes, relaxed ambient modes, authentic away-time catch-up, and permissioned VIP arrivals; explicitly made quests, collectibles, crafting, and larger worlds optional. Reordered the MVP to prove the lounge experience before the game layer.

- **9. Mission focus (v5):** Added the *v5 Scope* section and tagged non-mission sections [LATER] (including anonymous strangers and crafting). Added asynchronous VIP presence and a lightweight tokenized VIP link (section 3.13 B2); a Host regular and named regulars with labeled-fiction threads (section 3.7); arrival-time conversation, a content freshness floor, and an empty-bar fallback (section 3.15); user recognition memory with "a wrong memory is worse than none" (section 3.16). Reordered phases so VIPs precede progression; reduced the demo to the mission path; added one north-star metric per pillar.
