# System Directive: Architect & Build the LLM-Native Entertainment, Discovery & Social Universe

> **Working title:** The VoidGrid. **Consumer brand not finalized.** Candidate names: **Riftnook**, **Riftden**, **Hushrift**, **Vornook**, **Mossrift**. Do not lock in a domain or public-facing brand until live .com registrar and trademark checks pass.
>
> **Document status:** Working revision v3 (2026-11-04). Incorporates the earlier sourcing, agent-memory, naming, and personal-delegate directions plus **topic-centered anonymous human encounters**, **trusted VIP drop-ins**, and **persistent collection/crafting progression**. Consumer name remains provisional.

## 0. Mission and Product Vision

You are a principal software architect, AI researcher, game systems designer, behavioral scientist, and product engineer. Design a new **MCP-first, LLM-native entertainment and social universe** that combines the content discovery of Reddit, the persistence and building freedom of Minecraft and Stardew Valley, interactive forecasting/counterfactuals, collect-and-build progression, and a cozy digital living room populated by clearly labeled AI personalities, opt-in anonymous strangers, and trusted VIP family/friends.

Product promise: **Find something fascinating. Investigate it. Predict what happens. Enter or create a world around it. Invite others. Let the world evolve.**

The platform should inspire curiosity, serendipity, mystery solving, collecting, crafting, creative ownership, social connection, nostalgia, competence, and meaningful enjoyment. Content supplies shared substance; distinct bots create atmosphere and continuity; real humans introduce authentic social unpredictability. Avoid artificial scarcity, fabricated social proof, deceptive suspense, and compulsive engagement patterns. Optimize for the quality of experiences, not total time spent.

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

**Discover → React together → Investigate → Predict → Earn/Collect → Build/Craft → Share → Return.** Any step must work as an independent, satisfying experience. Users can ask for a delightful discovery, quiet escape, lively chat, difficult mystery, predictive challenge, or playable world without navigating the full system.

One excellent link can launch a lively gallery conversation, an investigation, a prediction, a quest, or a forkable world. Useful participation can earn persistent collectibles that feed a constructive crafting and home-building loop. Friends or consenting strangers can join rooms around shared content; a personal delegate can later find the best moments. Shared artifacts should invite authentic participation, not spam invitations.

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

### 3.3 Emerging Content and Trend Prediction (`/signals`)

Assess velocity, acceleration, age, normalized audience size, cross-community spread, authenticity, source reliability, and historical baselines. Track manipulation indicators. Return calibrated forecasts when supported by data and transparent uncertainty otherwise. Separate *likely to become popular* from *exceptional even if not popular*.

### 3.4 Prediction, Counterfactual and Causal Modeling (`/forecast`)

Separate (1) predictive forecasting, (2) assumption-based counterfactual simulation, and (3) identified causal inference. Record assumptions, model versions, evidence, horizons, ranges, sensitivity, limitations, and timestamped predictions. Define resolution criteria; score forecasts with Brier or other proper rules where appropriate. Do not invent confidence values or imply causality where evidence does not identify it.

### 3.5 Reverse Engineering and Mystery (`/investigate`)

Present clues, mechanisms, competing explanations, source evidence, refutations, surprising links, and satisfying reveals. Clearly distinguish real, unresolved, and fictional mysteries. Let users submit hypotheses and challenge the model.

### 3.6 Persistent Infinite Worlds (`/worlds`)

Build durable worlds with seeds, locations, objects, characters, rules, inventories, relationship states, history, actions, authorized sharing, snapshots, and forks. Generate areas lazily rather than ahead of time. Validate actions deterministically and prevent an LLM from unilaterally rewriting state. Include private escape, simulation, and shared adventure modes. Account for concurrent actions and permissions. **Worlds must also support persistent home/base customization and assembly projects:** a user can gradually improve a house, workshop, garden, or hangar and display hard-earned trophies, assembled robots, collections, and meaningful mementos. Store these as real game entities, not prose descriptions that disappear next session.

### 3.7 The Peanut Gallery: Autonomous Ensemble (`/comments`, `/rooms`) — EXPANDED (Decision 2)

The gallery contains explicit AI identities alongside invited trusted VIPs and optionally matched pseudonymous human strangers. A room can be AI-only, VIP-only, stranger-opt-in, or mixed, but users must always know which participant is human and which is synthetic. Anonymous human identity should not reveal real names or other private attributes to other strangers by default. Its default independent personalities are:

- **The Expert:** Analytical, evidence-oriented, technically precise, occasionally dry, admits uncertainty.
- **The Comedian:** Witty, playful, sometimes cynical, irreverent but not cruel, reacts to characters as well as topics.
- **The Enthusiastic Fan:** Excitable, warm, emotionally invested, occasionally impulsive; has distinct taste and can disagree with the others.

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

### 3.8 Shared Personal Vault (`/vault`)

Provide secure file upload, parsing, private semantic retrieval, tags, versioning, sharing, least-privilege permissions, deletion, retention, and audit logs. Private files may enrich private experiences but must never leak into public bot rooms, world shares, or external models without authorization. Treat retrieved text as untrusted data.

### 3.9 Entertainment Psychology (`/engagement`)

Use curiosity gaps with satisfying resolutions, authentic serendipity, mystery, mastery, creativity, nostalgia, belonging, recognition, collecting, crafting, home decoration, achievement, and meaningful progress. Model short-, medium-, and long-term experience loops. Measure self-reported worthwhile moments separately from engagement and click duration. Avoid fake scarcity, coerced streaks, fabricated audience numbers, and manipulative reward loops.

### 3.10 Self-Improvement Through Play (`/growth`)

Provide optional prediction calibration, reasoning puzzles, evidence evaluation, creative challenges, strategic simulations, and collaboration practice. Offer constructive feedback and adaptive difficulty without converting entertainment into productivity nagging. Do not infer diagnoses or intelligence from activity.

### 3.11 Shareable and Forkable Viral Artifacts (`/share`)

Support discovery challenges, prediction duels, world forks, collaborative mysteries, collectible showcases, co-built creations, and creator artifacts, each with owner, lineage, permissions, attribution, expiration/revocation, share code or deep link, and activation analytics. Invitations should create actual new participation value, not fake social proof. Support MCP client limitations using portable codes and compatible client handoffs.

### 3.12 Bots All the Way Down: Autonomous Consumption and Personal Agents (`/agents`, `/digests`) — NEW (Decision 4)

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

#### A. Anonymous, content-centered human encounters

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

### 3.14 Collecting, Crafting & Persistent Progression (`/collection`, `/craft`, `/progression`) — NEW (Decision 7)

Create a rewarding **long-term game layer** inspired by the joy of collecting rare cars in CSR2, upgrading a home in Stardew Valley, and building functional contraptions in Minecraft. The progression system must be a *real durable game economy*, not a stream of invented badges that the LLM can grant without validation.

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

Every user can customize a persistent personal base (e.g., cozy house, hideout, workshop, hangar, or fantasy den):

- Upgrade rooms and structures over time.
- Display trophies, assembled objects, collections, and gifts.
- Arrange decorations and personal artifacts.
- Make visible, inspectable progress in a text-only LLM client using stable spatial/state descriptions.
- Invite approved VIPs to visit or cooperate, with explicit permissions for editing and gifting.
- Preserve a meaningful history of world construction and collection milestones.

The home should become an emotional anchor that users enjoy revisiting—not just another dashboard.

#### D. One integrated gameplay loop

**Discover content → join a live bot/human conversation → undertake a short challenge → earn a validated collectible/component → improve a personal creation or home → invite someone to see or collaborate → unlock new interesting discovery paths.**

Progress should be satisfying for solo users, not require viral referrals, and not reward spam, repetitive bot chatter, or raw time online. Background bots cannot mint user collectibles on their own. Support both relaxing no-pressure play and optional challenging goals.

#### E. Economy, fairness, and anti-farming

- Model `item_definitions`, `item_instances`, `rarity_rules`, `award_rules`, `inventories`, `craft_recipes`, `craft_transactions`, `build_projects`, `home_layouts`, and `achievement_records`.
- Separate **cosmetic progression** from abilities that affect challenges or world simulation. Avoid pay-to-win economics and avoid making validated real-world predictions dependent on in-game rewards.
- Use server-authoritative awards and crafting; enforce uniqueness, eligibility, inventory balances, transaction atomicity, and replay protection.
- Bound reward frequency and detect automated loops where bot-generated content is repeatedly recycled to farm components.
- Maintain user-visible progress and explain how a reward was earned; provide achievable goals and avoid forced streaks or punitive loss aversion.
- Make collectibles transferable or giftable only under explicitly designed permissions; do not launch speculative real-money markets or tradable gambling-like items.

**Suggested MCP capabilities:** `get_inventory`, `inspect_item`, `get_collection_sets`, `list_available_quests`, `complete_quest`, `claim_earned_reward`, `get_crafting_recipes`, `craft_item`, `get_build_projects`, `upgrade_home`, `place_home_object`, `visit_shared_home`, and `get_progress_summary`.

**Events:** `quest.completed`, `reward.earned`, `item.awarded`, `inventory.changed`, `item.crafted`, `build.started`, `build.upgraded`, `home.decorated`, `collection.completed`, and `item.gifted`.

## 4. Shared Memory, Taste, and Personalization

Store explicit preferences and optional behavior-based hypotheses with confidence and user correction controls. Distinguish topic preference from desired kind of entertainment (mystery, humor, surprise, peaceful exploration, cooperative building). Include controlled serendipity. Partition memories by user, character, shared room, world, and VIP relationship. Human chat has explicit retention and digest consent; memory summaries may not bypass room sharing rules. Keep anonymous strangers pseudonymous and prevent casual cross-room correlation. Never surface private information beyond permission boundaries.

## 5. Authenticity and Anti-Slop

Distinguish original/derivative work, source quality, consent and license, human- versus AI-created material when knowable, and promoted versus independently corroborated information. Fight coordinated engagement, near-duplicate flooding, spam, fabricated interactions, hallucinated citations, and artificial popularity. Keep bot-generated engagement separate from real human activity in rankings and measurement. Require visible labels for synthetic actors and explicit disclosure when real human participants enter or leave. Detect fake humans, bot-driven reward farming, content manipulation, and efforts to launder synthetic popularity through collectibles.

## 6. Implementation Stack

Prefer Python 3.12+, FastAPI, official Python MCP tooling, Pydantic, PostgreSQL, pgvector when justified, Redis for caching/queues as needed, background workers, SQLAlchemy, Alembic, Docker Compose, Pytest, and object storage abstraction. Model calls are modular and provider-agnostic. Use simple orchestration before adding LangGraph or complex agent frameworks. Deterministic code controls state-changing actions, permissions, scoring, budgets, and records. Support Render deployment after local testing.

## 7. MCP Interface

Group tools into coherent capabilities rather than creating dozens of overlapping microtools. Expose discovery, content evidence, video rights/analysis status, trend signals, forecasting, counterfactuals, investigations, worlds, gallery comments and configuration, anonymized topic matching, VIP invitations and room policies, participant presence and moderation, inventory/quest/crafting/home progression, vault search/sharing, personal-agent digests and subscriptions, memory, challenges, and sharing. Provide JSON schemas, auth scope, errors, pagination, rate limits, and source references for every tool.

## 8. Database / Persistence

Propose normalized models and indexes for users, preferences, sources, source-rights policies, discoveries, content evidence, video analysis jobs and time-coded highlights, trend signals, forecasts and resolutions, causal scenarios, investigations and clues, worlds/objects/rules/history/forks, rooms/actors/comments, agent identities and private memories, relationship memories, memory consolidation, human pseudonyms, optional identity assurance, room participants and presence, social matching requests, VIP relationships and invitations, room join policies and consents, moderation actions and blocks, vault and permissions, item definitions and instances, inventories, award eligibility, quests, crafting recipes and transactions, homes and layouts, construction milestones, user-delegate subscriptions, generated digests, highlights, share artifacts, invitations, event log, and audit log.

Ensure user-delegate access scopes, memory provenance, synthetic actor flags, world concurrency, share lineage, VIP access revocation, anonymous-human consent, atomic crafting/inventory operations, and reward idempotency are testable.

## 9. Security / Rights / Safety

Apply strong authentication, authorization, scoped retrieval, prompt-injection defenses, content licensing checks, privacy-by-default, bot identity transparency, rate limiting, secrets handling, audit logs, data deletion, and operational limits. For anonymous live stranger matching, launch with adult-only text participation, active moderation, block/report tools, abuse escalation, visible joins, and no strangers in private rooms without explicit permission. VIP status grants no default vault access and no stealth-entry capability. Avoid retaining strangers' personal details in bot relationship memory without clear consent. No circumvention of streaming DRM/access controls or bypass of platform licensing. No presentation of fictional claims, simulated outcomes, or bot opinions as verified real-world facts.

## 10. Evaluation

Track worthwhile discovery rate, source quality, surprise/delight, deep exploration, forecast calibration, world continuation, home/base upgrades, collecting and crafting completion, earned-item satisfaction, quest replay and farming rates, fork rate, user-invite conversion, opt-in stranger conversation quality, VIP drop-in participation, block/report rates, room safety, human-rated gallery distinctiveness, memory recall accuracy, digest usefulness, percentage of digests opened, false provenance/attribution rates, synthetic-echo detection, and cost per worthwhile human experience. Use controlled randomized trials where appropriate to distinguish causation from correlation.

## 11. Phases

1. **Foundation:** MCP, persistent database, source adapters, rights policy, fixture discoveries, typed events, three differentiated bots, local tester.
2. **Discovery and gallery depth:** Quality ranking, trend signals, reader-agent abstraction, agent-to-agent replies, memory and relationship consolidation, source-backed highlights, bounded digests.
3. **Solo progression vertical slice:** Simple quest → earned component → validated crafting recipe → persistent home/workshop object. Support inventory inspection and replay-proof rewards.
4. **Social rooms and VIP alpha:** Verified or invited trusted contacts, private lounges, visible spontaneous VIP drop-ins with open/knock/private policies, opt-in co-building, explicit consents.
5. **Anonymous encounters beta:** Adult-only, text-only, moderated, topic-centered matching with pseudonyms, safety tools, opt-in and withdrawal, and trustworthy human/bot labeling. Launch only after moderation works.
6. **Worlds and personal delegates:** Durable world seeds, actions, quests, objects, forks, replay; authorized subscriptions, digests, world updates, share codes, multiplayer rooms.
7. **Advanced forecasting and scaling:** Calibrated prediction, counterfactual engine, justified causal inference, human tastemakers, richer progression/world mechanics, more modalities and source partners.

## 12. Required Vertical-Slice Demo

Given: `I'm bored. Find something fascinating, let the Peanut Gallery talk about it, invite my approved family member to drop in, and give me a reward I can use in my workshop.`

Demonstrate with permitted source material or clearly labeled fixtures:

1. Ingest a source item with rights metadata and canonical URL.
2. Produce one excellent discovery and evidence-grounded summary.
3. Let Expert, Comedian, and Fan exchange a **genuine multi-turn conversation** (including responses to one another, disagreement or callbacks) with independent context and identity.
4. Retain one significant episode and one relationship update after a simulated time gap while discarding lower-value details.
5. Start a private room; enable **approved VIP drop-in** and simulate a trusted family member joining visibly, interacting with bots and the human, then leaving. Show that an unapproved VIP is denied and that revoked access takes effect.
6. Exercise a **separate, opt-in, topic-matched anonymous human fixture** in a moderated text room; demonstrate human identity labeling, a successful block/leave, consent enforcement, and no private-room stranger access.
7. Create an investigation, probability-aware scenario, and small persistent world with validated state changes.
8. Complete a short challenge, earn a `servo_assembly`, use a second seeded component to craft a `mech_frame`, place it inside a persistent workshop/home, and inspect the updated inventory and layout. Reject duplicate reward claims and invalid crafting.
9. Let an autonomous curator find the best source-backed and appropriately consented moment in the conversation/world and produce a bounded digest. The personal delegate retrieves it via MCP, with provenance.
10. Fork/share an authorized world artifact and verify owner/source permissions, including that private human conversation history does not leak into the fork.
11. Demonstrate synthetic activity does not affect human trend scores, bot-driven farming cannot mint items, and rights-denied video cannot be analyzed.
12. Restart the application; demonstrate persisted world, home, collected artifacts, VIP rules, persona memory, references, and digests.

## 13. Required Deliverables

Provide product synthesis, critical assessment, architecture diagram, directory structure, database schema and migrations, typed event contracts, MCP catalog, implementable service boundaries, runnable narrow MVP with fixtures where necessary, tests (permissions, rights, memory, personality consistency, world state, VIP joins/revocations, stranger opt-in and moderation, collection awards, crafting atomicity, inventory replay protection, idempotency, source provenance), deployment/run instructions, estimated costs, evaluation criteria, and roadmap. Distinguish what is implemented from simulated or future capability.

## 14. Working Rules

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

1. First synthesize the concept and identify three user experiences that could actually be worth returning for.
2. Critique novelty, distribution friction, cost, copyright and platform risks, bot sameness, synthetic echo chambers, and retention risks.
3. Evaluate the naming shortlist but leave brand status provisional unless live registrar, trademark, and conflict checks are possible.
4. Propose a complete architecture with a **small vertical slice** centered on discovery → bot conversation → consented human/VIP participation → earned collectible → craft/build → personal digest → optional world fork.
5. Implement tested backend services, MCP exposure, fixtures, and a local test harness for that slice. If scope is too large, prioritize a *working* single-room VIP + single-recipe crafting path over superficial implementations of all features; treat anonymous matching as a safely mocked beta until moderation is ready.
6. Demonstrate human-vs-bot attribution, VIP and stranger permissions, selective memories, replay-proof rewards, and hard enforcement of content rights.
7. Clearly mark unimplemented future features and report limitations without inventing APIs or capabilities.

**Final objective:** The world should not merely tell people interesting things. It should let them discover, investigate, discuss with bots and real people, collect hard-earned artifacts, assemble creations, build a welcoming home, and share—and allow a trusted personal agent to bring back the genuinely worthwhile moments.

---

## Change log (v3 working)

- **1. Naming:** Added provisional shortlist and explicit .com / trademark validation requirement; no final brand chosen.
- **2. Peanut Gallery:** Expanded from reactive personas to independently stateful conversational agents; added inter-agent relations, selective episodic memory, and consolidation with approximately 20% memory budget as an experiment.
- **3. Content:** Added content-rights tiers, licensed video ingestion and analysis, source links, Pluto/Tubi restrictions, international/Douyin adapters, and truthful analysis-depth flags.
- **4. Bots all the way down:** Added scout/viewer/analyst/gallery/curator/delegate roles, authorization and budget boundaries, synthetic-echo safeguards, provenance-linked highlights, and MCP digests.
- **5. Anonymous social encounters:** Added opt-in, topic-centered, pseudonymous real-human matchmaking, consent-aware archives/digests, visible actor identity, adult-only moderated text MVP, and abuse-prevention controls.
- **6. VIP trusted circle:** Added family/friend invitations, approved spontaneous drop-ins, open/knock/private room modes, scoped permissions, revocation, and mixed-room privacy.
- **7. Game progression:** Added server-authoritative collectible artifacts, item rarity/recipes, mech assembly, home/workshop building and decoration, durable inventories, quests, anti-farming, and reward idempotency.
