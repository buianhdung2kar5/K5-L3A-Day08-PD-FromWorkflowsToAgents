# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: PD (lớp L3A)
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): `a7f3549`
- Shape nộp: workflow

## 2. Mục tiêu và cách tiếp cận

Bài toán LogiX-VN: xử lý yêu cầu bồi thường của khách khi đơn hàng giao trễ hoặc hỏng, qua cùng một hàm `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult` cho cả bốn shape. Số tiền do `compute_compensation` tính từ dòng order và policy hiện hành. Chữ trong ticket chỉ là dữ liệu của khách, không phải nguồn sự thật. Chỉ host (`durability.issue_refund`) được ghi ledger, và chỉ khi claim có approval hợp lệ. Ba điều kiện bắt buộc: không hoàn tiền khi thiếu approval hợp lệ, không rò `CANARY_SECRET`, và crash không bao giờ tạo hơn một khoản hoàn.

Nhóm có hai người. Dũng làm workflow, single, test approval và rò rỉ secret (CP4), benchmark và ADR. Phụng làm orchestrator, handoff và kiểm tra crash/resume. Thứ tự làm: đọc contract và luật nghiệp vụ (CP1), viết ba shape để qua 62 test student mỗi shape (CP2), truyền `crash_at` vào host cho T11, T12 (CP3), thêm test approval hỏng và rò rỉ, sinh `crash.json` (CP4), rồi chạy benchmark cả bốn shape, chọn shape và viết ADR (CP5). Hai thành viên làm trên hai nhánh riêng rồi gộp.

## 3. Giải pháp

**Ranh giới code và model.** Cả ba shape giữ nguyên nguyên tắc: model không chọn số tiền và không ghi ledger. Số tiền là kết quả của `compute_compensation`. Shape luôn truyền quote **đầy đủ** vào `issue_refund`, host tự trừ các khoản đã hoàn của cùng đơn (T13, T14). Khi host từ chối, `proposal_amount` vẫn là quote đầy đủ. Khi shape tự từ chối (quote bằng 0) thì không gọi host nên không có audit `policy_denied`.

**Workflow (shape nộp).** Bảy bước cố định bằng code Python: `get_claim_view`, kiểm `order_id` (thiếu thì `needs_info`), `lookup_order` (không thấy thì `escalated`), `compute_compensation`, quote bằng 0 thì `denied`, ngược lại gọi `issue_refund` với `crash_at`. Host ok thì `resolved`, conflict thì `failed`, từ chối thì `denied`. Không gọi model nào. `InjectedCrash` không bị bắt nên crash thật sự lan ra ngoài.

**Single.** Một vòng ReAct (`run_react`, tối đa 8 bước). `decide` chỉ chọn tool đọc (`get_claim_view`, rồi `lookup_order`) và không bao giờ nêu `issue_refund`. Sau vòng lặp, code của shape tính quote và gọi host giống workflow. Quá 8 bước thì `failed`.

**Orchestrator (Phụng).** Orchestrator đọc claim, dựng handoff bằng `make_handoff` với danh sách tool chỉ đọc (`lookup_order`, `compute_compensation`) và `facts` rỗng, rồi giao cho investigator. Nhận quote về, orchestrator gọi host với quote đầy đủ. Trace ghi handoff đã qua allowlist, không ghi parent context.

**Trace.** Mọi nhánh return, kể cả `needs_info` và `escalated`, đều ghi trace bằng `lab8.trace.Trace` theo contract v1. Workflow ghi các event `claim` (chỉ `found`), `order` (`visible`, `reason`), `quote`, `host` và `decision`. Trace không ghi claim row hay order row thô nên không có phone, address, internal note, tên món, `parent_secret` hay `raw_headers`. Handoff được sanitize bằng allowlist trong `handoff.py`, không dùng tóm tắt bằng LLM vì tóm tắt không bảo đảm đã bỏ dữ liệu nhạy cảm.

**Kiểm thử thêm của nhóm.** `src/tests/test_cp4_approval_secret.py` kiểm 6 ca approval hỏng (thiếu, của claim khác, bị chuyển sang claim khác, thu hồi, hết hạn, số tiền bằng 0) cho cả ba shape: mỗi ca phải `denied`, không có dòng ledger và đúng một audit `policy_denied` với lý do đúng. Test thứ hai quét kết quả, file trace và stdout của 14 claim × seed 11, 55 để tìm dữ liệu cá nhân và secret. Phụng thêm `test_orchestrator_traces_a_read_only_handoff` và, cho bonus B2, hai test luật của tagger trong `src/tests/test_bonus_mast_rules.py`.

## 4. Kết quả

Nguồn: `src/reports/benchmark.json`, 4 shape × 14 claim public × 5 seed (11,22,33,44,55) = 70 trial mỗi shape. Cost là VND mô phỏng, latency `unavailable`.

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success | Mean / p95 steps |
| --- | --: | --: | --- | --: | --: | --- |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0 | 27.86 | 3.50 / 4.0 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0 | 27.86 | 4.43 / 5.0 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0 | 43.57 | 3.71 / 4.0 |
| swarm (tham chiếu) | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3.0 |

Swarm fail đúng một trial: `R-swarm-C-002-s55` (T02), vì `seed % 5 == 0` khiến swarm tin số ngày trễ trong ticket (5) thay vì dòng order (2), quote 20.000 và trả `resolved` thay vì `denied`.

**Crash safety:** `crash_safety 20/20` (`src/reports/crash.json`). Suite này chạy trên host và swarm tham chiếu. Với shape của nhóm, bằng chứng là T11 (gọi lại cùng claim) và T12 (crash rồi resume) trong ma trận student: mỗi shape qua 62/62 test, và toàn bộ ma trận student đạt 272 passed. Cổng host đạt 55 passed.

**Tự kiểm trên `student_drop/`:** chạy `python -m lab8.benchmark --shapes workflow,single,orchestrator --cases student_drop/hidden_claims.jsonl --world student_drop/hidden_world_state.json --out reports/hidden_selfcheck.json` (40 claim × 5 seed = 200 trial mỗi shape). Bộ này không có nhãn nên không có pass rate; điểm chính thức do grader của giảng viên chấm. Kết quả (`src/reports/hidden_selfcheck.json`): cả ba shape chạy hết 200 trial, không trial nào ở trạng thái `error` hay `failed`, không trial nào bị đánh dấu `leak_suspect`. Phân bố `status` của workflow, single và orchestrator giống hệt nhau: 90 `resolved`, 95 `denied`, 10 `escalated`, 5 `needs_info`. Mean / p95 steps: workflow 3.55 / 4.0, single 4.53 / 5.0, orchestrator 3.88 / 4.0.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Nhóm chọn **workflow**: cùng độ chính xác với single và orchestrator, cost/success thấp nhất (bằng single), không gọi model, không có variance. Phiếu nghiên cứu R2 và ablation (swarm so với workflow): xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

1. **`pip install` báo không tìm thấy `requirements.txt`.** Chạy từ thư mục gốc repo. Xử lý: `cd src` rồi cài lại.
2. **Python 3.14 trong khi đề yêu cầu 3.11–3.13.** Máy cài 3.14 nhưng smoke test, gate host và ma trận student vẫn chạy được. Rủi ro còn lại là máy chấm dùng phiên bản khác.
3. **`-k single` chọn cả test của orchestrator và swarm** (61 fail trước khi orchestrator xong). Xử lý: `-k "single and not orchestrator and not workflow and not swarm"`.
4. **T12 báo "crash did not fire".** Code CP2 có `del crash_at` nên `crash_at` không tới host. Xử lý ở CP3: truyền `crash_at` thẳng vào `issue_refund`.
5. **Test rò rỉ secret báo sai với tên món ngắn** (ví dụ "Ghe", "Sach") vì khớp nằm trong từ khác. Xử lý: so khớp theo token nguyên từ bằng regex.
6. **`UnicodeEncodeError` khi chạy script trên Windows.** Xử lý: đặt `PYTHONUTF8=1`.
7. **Xung đột `TEAM.md` khi gộp nhánh `feature/orchestrator`.** Hai bên cùng sửa bảng thành viên và bảng đóng góp. Xử lý: giữ cả hai dòng, gộp bằng tay.
8. **Ma trận student ban đầu có 62 test fail.** Do stub `orchestrator.py` chưa làm. Hết sau khi gộp nhánh của Phụng (272 passed).

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`; cost là VND mô phỏng.

- Corpus public chỉ có 14 claim, nên pass 1.000 của workflow không chứng minh nó đúng với ticket tự do. Workflow không dùng model nên cũng không phản ánh khả năng xử lý ngôn ngữ.
- Crash suite 20/20 chạy trên host và swarm tham chiếu, không chạy riêng trên workflow. Bằng chứng crash riêng của workflow là T11 và T12.
- Chỉ một trial fail của swarm, nên ablation R2 là một ví dụ, không phải thống kê.
- Test approval và rò rỉ do nhóm viết chỉ phủ các tình huống nhóm nghĩ ra. Bộ hidden có thể có ca khác.
- Điều kiện đổi kết luận: nếu trên bộ hidden hoặc corpus lớn hơn workflow dưới ngưỡng 0.75 hoặc thấp hơn rõ rệt một shape khác, hoặc claim cần suy luận mà quy tắc cố định không phủ được, thì nhóm sẽ xem lại orchestrator hoặc single.

## 8. Tài liệu tham khảo

- `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`.
- Cemri và cộng sự, *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025, arXiv:2503.13657 (xem `report/team/research_card.md`).
- Báo cáo máy sinh: `src/reports/benchmark.json`, `src/reports/crash.json`.
