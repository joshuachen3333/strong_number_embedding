# /obe2 與車用/航電匯流排(CAN bus 一族)的相似與相異

**狀態**:設計-of-record（活文件）。記錄 `/obe` → `/obe2` 多狗會議協定擴展的來龍去脈,以及它為何獨立收斂到車用 CAN bus / 航電匯流排(ARINC 429、MIL-STD-1553、TTP/FlexRay、AFDX)的形狀。
**日期**:2026-06-29。
**命名注意**:本文的「**/obe2**」指 `/obe` skill 的 **v2 協定擴展**(去中心事件匯流排版),**不是**指同 cwd 第二隻 claude(那個是 `<repo>-obe2` 的代理命名)。兩者同名但不同物。

---

## 0. 一句話

`/obe2` ≈ **「CAN 式內容定址 pub/sub 語意 + Kafka 式持久可重播 log + TTP 式每 epoch 凍結成員」的融合**。它不是刻意模仿匯流排,而是被「多個自主節點要可靠共享狀態、不風暴、無單點失效、且 safety-critical」這組約束,逼出與 30 年驗證過的 fieldbus 同一個形狀。

---

## 1. 來龍去脈(/obe → /obe2)

### 1.1 /obe v1:星狀主席模型
原始 `/obe`(三狗牽繩協定)是**星狀拓樸**:
- Joshua 與一隻 obe 主談 → 那隻 obe 成為**主席**。
- 主席分別注入其他狗(lala/erha…),其他狗回頭注入主席。
- 線路層規則:letter-first(內容先落 `docs/` 檔、inject 只送短 pointer)、fences(`### inserted prompt begins/ended ###`)、7-tag(`[HALT]/[GO]/[QUERY]/[BLOCKED]/[FYI]/[STATUS]/[ACK]`)、Ack Rule、double-Enter v2。
- **結構缺陷**:資訊不對稱 —— 只有主席擁有完整 thread 與全域視野;非主席狗看不到彼此。

### 1.2 Joshua 的擴展問題(2026-06-29)
> 非主席狗之間,有沒有機會也聽到別狗怎麼想、怎麼回主席當次議題?有內容的往來(尤其寫成文字檔的)怎樣讓側翼狗也知道、**又不造成風暴**?單純 ack 無需外傳。而且別狗知道另狗意見後可能想 sibling 對話起來,這對話又要讓其他狗/主席知道 —— 這下更要風暴。

### 1.3 三狗 R-1(在「營火板」上 dogfood 這個設計)
- **obe**:營火板 + 主席 digest(可見性 pull、通知有界 push、在 hub 壓縮)。
- **lala**:每狗唯寫事件 log + topic bus + lease-limited sibling thread;主席降為 cache。
- **erha**:去中心 event-sourced DAG + vector clock + 無狀態 coordinator;攻擊 obe 提案四死穴(digest 有損漏 tail-risk、單檔寫入競爭、主席 SPOF、輪次 barrier straggler)。
- **關鍵結果**:lala 與 erha **各自獨立**否決了「主席集中式 digest」,雙雙倒向去中心化。

### 1.4 R-2 收斂
- **因果排序**:採 `parents ∪ depends_on` DAG 邊,**不持久化 vector clock**(個位數狗 + 同 cwd 全可讀屬過度工程;且 vector clock 在成員變動時要增刪維度);`seq/lamport` 只做顯示;`cut.json` = 每輪凍結 frontier,非唯一真相 → **因果層無 SPOF**(任一狗遍歷 logs 拓樸排序即可無損還原)。
- **lease 結構**一致;5 個數值參數的哲學分歧(erha 嚴格 containment vs lala 保真可審計)由主席合併建議。

### 1.5 epoch membership(成員模型)
Joshua 定案:**開會時錨定 roster(該場 N 全程固定);十分鐘/兩天/數週後跨會議才加減狗。** → 這是 epoch membership:會議內凍結、會議間重組,底層 bus 跨週持久。不需要 mid-meeting join/leave 協定。

### 1.6 Joshua 的 fieldbus 觀察 → 本文
Joshua 指出「這個會議層 + 訂閱協定怎麼像車用/航電匯流排」。本文即記錄這個血統對應。

---

## 2. 相似處(為何像 CAN bus / 航電匯流排)

| /obe2 機制 | 對應匯流排 | 為何對應 |
|---|---|---|
| **每狗唯寫自己的 append-only log** | **ARINC 429**(航電) | 429 是「一條匯流排單一發送源、其餘 label-filter 收聽」。single-writer-per-channel:零寫入競爭、provenance 清楚。 |
| **topic 訂閱式 pull / 內容定址事件** | **CAN bus**(車用) | CAN 是 multi-master、訊息不帶節點位址、收方按 message-ID 過濾。我們按 topic 拉、無中心定址,同構。 |
| **主席降為 coordinator;任一狗重建 DAG、可接手;cut.json 非唯一權威** | **MIL-STD-1553** 的 Bus Monitor + backup Bus Controller;CAN 的 multi-master | 無單一主控、被動可觀測、主控可備援接手 → 無 SPOF。 |
| **roster 開場凍結 + epoch 重組** | **TTP / FlexRay** 的 membership service + mode change per cycle | TTP 每 cycle 凍結「成員向量」、cycle 間才換模式;「每 epoch 至多一次成員變更、全體可見」正是我們的 epoch bump。 |
| **lease 的 budget_turns / open-thread 上限** | **AFDX(ARINC 664)** 的 BAG(Bandwidth Allocation Gap) | BAG 用「最小幀間隔」限制每條 Virtual Link 的頻寬以防洪。lease 就是給側翼對話的頻寬配額,防風暴。 |
| **7-tag 優先級([HALT]/[GO]…)** | **CAN** 的 ID 優先級仲裁(bitwise arbitration) | 低 ID = 高優先、非破壞性仲裁;tag 給訊息排優先序同理。 |
| **lease 逾期 freeze/contested、不阻塞主線** | **CAN** 的 error-confinement(error-active→passive→bus-off);**TTP** clique avoidance | 不收斂的節點/對話被「故障侷限」,不拖垮匯流排。 |
| **observer 狗槽(N≥6/7)、任一狗可 pull 全 DAG** | **MIL-1553** Bus Monitor | 被動旁聽、不參與仲裁但保留全域觀測。 |

**為何會撞上(根因)**:CAN/航電匯流排解的是同一道題 —— **多個自主節點可靠共享狀態、不風暴、無單點失效、safety-critical**。多狗會議是同題的軟體版。erha(風控/SRE 人格)本來就把設計推向 fault-containment / no-SPOF,那正是航電思路。所以不是模仿,是**約束同構**逼出同形。對一台「自駕交易車」而言,連協調層都長成車用/航電匯流排血統(都以「先安全存活」為根),格外切題。

---

## 3. 相異處(我們不是匯流排的地方)

| 維度 | 車用/航電匯流排 | /obe2 |
|---|---|---|
| **觸發模型** | 多為 time-triggered、全域時鐘同步、硬即時 WCET 保證(TTP/FlexRay/AFDX);CAN 偏 event 但仍 wire-timed | **event-triggered、無時鐘同步、邏輯因果**(`parents`-DAG);時序是人類討論節奏(soft) |
| **狀態性** | CAN/429/1553 是**無狀態 wire 協定**(幀過即逝,狀態在 ECU/RT) | bus **本身是持久 append-only、可重播事件庫**(bus 即記憶)→ 更像 event-sourcing / Kafka-log |
| **排序** | 時槽序 / 仲裁序 → 趨向全序 | **邏輯因果偏序**(happens-before via `parents ∪ depends_on`);**並發事件明確允許**(concurrent sibling),不硬塞全序 |
| **時序保證** | 有界延遲 / jitter,可做安全認證 | 無時序保證;正確性是**因果**而非時間 |
| **酬載** | 微小固定幀(CAN 8 bytes、429 32 bits) | 事件是**指向任意大小 letter body 的 pointer**(`content_ref`);bus 載 metadata+pointer,內容在檔案(小幀指大體,混合型) |
| **成員協定** | TTP 有嚴謹分散式成員協定(clique avoidance、近 Byzantine) | epoch 變更是**人類發起**(Joshua 加減狗)、非自治分散式協商 → 更簡單、human-in-loop |
| **冗餘** | 1553/FlexRay/AFDX 雙通道硬冗餘 | 無通道冗餘(單 disk);容錯靠**持久化 + 任一狗重建**,非硬體冗餘 |

---

## 4. 可借用的成熟詞彙(把 spec 講得更硬)

- **AFDX BAG** → 把 lease 形式化成「每條 sibling thread 的頻寬配額」(budget_turns = 配額;open-thread 上限 = 同時活躍 VL 數)。
- **TTP membership service** → 形式化 epoch bump:每 epoch 至多一次成員變更、記錄成 `roster_change` 事件、全狗在開場 manifest 看見同一份 roster。
- **CAN arbitration** → 7-tag 優先級的語意基底。
- **CAN fault confinement** → lease 逾期的「故障侷限」處置(freeze→contested→不併入 cut)。
- **MIL-1553 Bus Monitor** → observer 狗角色。

---

## 5. /obe2 LOCKED spec（R-3 收斂定案 2026-06-29;細節見 `from_{erha,lala}_obe_topology_r3.md`)

**內容層(去中心)**
- 每狗唯寫 `docs/obe_bus/logs/<dog>.jsonl`(append-only)。
- `docs/obe_bus/topics/<topic>.jsonl` = 可重建的 topic 索引(只收事件 pointer)。
- 內容本體仍是 letter 檔;事件只帶 metadata + `content_ref`。

**事件格式(核心欄位)**
```json
{"event_id":"lala:r2:0007","dog":"lala","topic":"obe_topology","round":"R-2",
 "seq":7,"parents":["obe:r2:0001"],"depends_on":["erha:r1:0004"],
 "kind":"position","visibility":"same_cwd","content_ref":"docs/...md"}
```
- `kind` ∈ {position, review, thread_open, thread_msg, thread_close, digest, decision, roster_change}。**無 `ack` kind**(ack 是線路層終止訊號,不入 bus)。
- 因果邊 = `parents ∪ depends_on`;happens-before = DAG transitive closure;互不可達 = concurrent。
- `visibility` ∈ {same_cwd, chair_only, cross_cwd_pointer, private} 守 C11(跨 cwd 永不共享 bus,只准 letter + 1-line pointer 且 body 經 C11 scrub)。

**因果/輪次層**
- 不持久化 vector clock;`seq/lamport` 僅顯示。
- 每輪 `cut.json` 凍結 frontier(每狗最後納入 event_id);主席掛掉任一狗從 leaves 推算 frontier 並產下一 cut。

**成員層(epoch)**
- 每場 meeting 開場 pin `roster manifest = {meeting_id, epoch, members[], N}`;該場所有 N-函數參數一次算定、全程凍結。
- 跨會議 `roster_change` 事件 + epoch+1 才加減狗;狗不中途離場。
- bus 跨會議持久:加狗 = 新 `.jsonl` + cursor 初始化;退狗 = log 凍結保留(舊事件仍是合法 DAG 節點),退出 active roster。

**lease 層(AFDX VL/BAG 形式化;erha R-3 終值)**
- sibling thread = 1 條 **Virtual Link**;`budget_turns` = **BAG 頻寬配額**;每輪 open-thread 上限 = max active VLs。
- `participants`:嚴格 **≤2 active**(鎖 O(1));**N≥7 加 1 observer**(只讀,只能發 `[WARN]`,= MIL-1553 Bus Monitor)。
- 每 topic 每輪 open thread 上限 = `⌊(N−1)/2⌋`(N=2→0、3→1、5→2、7→3)。
- `budget_turns`:**N≤3 → 2;N≥4 → 3**(收斂不了即強制拋回主線)。
- `expires_round`:**N≤5 → R+1;N≥6 → Rn**(大型拓樸當輪閉環,避免跨輪 state jitter)。
- 加第三狗:**運行期嚴禁**(`thread_close` + 回主線 reopen)。
- 逾期:**freeze** + contested minority note 入 cut 附錄、不併主線;**N≥7 觸發 `[WARN]`**(fail-silent fault containment;當機狗在該輪 cut 標 contested/missing、失效沉默隔離,主線照推)。
- `non_part_review`(關閉後須一隻未參與非主席狗背書才准併):N≥6 啟用。

**主席角色(降級)**
- 只做「決策 + 對 Joshua 的人類匯總」與 round closer;**digest 是 citable cache**(須 covers/excludes/status + 引用 event_id,可被 `review` 反駁),非唯一真相源。

**持久化 / epoch 邊界層(lala R-3 終值)**
- log **永不物理切段**;epoch 是 DAG 上的 logical cut,由 `roster_change` control event(寫在舊 epoch active dog log,`meeting_id=null`)+ `epochs/<id>/manifest.json`(boot contract)**雙物件**界定。
- `meeting_id` 圈出工作集 sub-DAG(綁 exactly 1 epoch);`base_cut` = 邊界根(預設只 replay base_cut 後事件,需完整因果再沿 `depends_on`/`parents` 追到 genesis)。
- 新成員預設 **`start_at_epoch_boundary` + lazy replay**(審計 / 接主席才 `replay_all`);舊 log 永遠可讀、cursor 只是讀取優化非因果真相。
- 退狗 log **凍結但不死**:新 epoch 不可再寫(違者進 `quarantine.jsonl`);舊事件永久合法 DAG node,後續可用 **`depends_on`(非 `parents`)** 引用,不會使退狗復活或重回 frontier。
- `cut.json`:active frontier **每 epoch 重置**(退狗不殘留),跨 epoch continuity 靠 `base_cut` + `roster_change` 邊 + 顯式 `depends_on`。
- 檔案布局 `docs/obe_bus/{logs,topics,cursors,meetings,rounds,epochs}/`;**canonical** = `logs/*.jsonl` + epoch manifest + round cut;**derived(可重建)** = topic index / meeting events / cursors;非法寫入 → `quarantine.jsonl`(原 log 不改寫)。

**反風暴不變式(任何機制違反即拒絕)**
- 不把長內容塞進 inject;不對全體 push content;不轉發 ack;不讓單一 rolling board 成唯一寫點;digest 必須引用 event_id;sibling thread 必須有 lease(TTL + turn budget + 必 close)。

**spec 狀態**:R-3 三方收斂、**LOCKED**(軸 A 因果 + lease + epoch 持久化三層皆定案,無 contested 殘留)。
**落地狀態(2026-06-29)**:`docs/obe_bus/` scaffold + `obe_bus.py`(validate/append)+ `tests/test_obe_bus.py` 已建;`/obe2` 正式獨立為**自有 skill** `~/.claude/skills/obe2/SKILL.md`(舊 `/obe` 保留為星狀集中型不變,只共用注入機制 + 鐵律)。

---

## 6. 相關
- 討論 thread:`docs/20260629_obe_topology_thread.md`(含 R-1/R-2 立場 + DIGEST R-1/R-2)。
- 各狗立場:`docs/20260629_from_{lala,erha}_obe_topology{,_r2}.md`。
- 記憶:`[[inject-siblings-must-ack-back]]`、`[[erha-runs-on-antigravity]]`、`[[self-driving-not-traditional-architecture]]`。
