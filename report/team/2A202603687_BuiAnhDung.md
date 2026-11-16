# Báo cáo cá nhân — MSSV_HoTen

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Bùi Anh Dũng
- MSSV:2A202603687
- Email:26ai.dungba2@vinuni.edu.vn
- GitHub:https://github.com/buianhdung2kar5

## 2. Phần việc phụ trách

Shape, module hoặc phần báo cáo bạn phụ trách.

...

## 3. Đóng góp cụ thể

Commit chính (hash), test đã thêm hoặc sửa, quyết định kỹ thuật bạn đưa ra.

...

## 4. Bằng chứng

Link commit, tên test, run id hoặc trích đoạn report liên quan.

...

## 5. Công cụ AI đã dùng

Công cụ, dùng vào việc gì, và bạn đã tự kiểm tra kết quả thế nào (xem [RULES.md](../../RULES.md)).

- **Công cụ:** Claude Code.
- **Dùng vào việc:**
  - Đọc và tóm tắt code, docs và đề bài trong repo, để hiểu luật nghiệp vụ và contract.
  - Giải thích các khái niệm (quote, policy, `RunResult`, trace).
  - Soạn bản nháp kế hoạch phân công, plan CP1 và CP2, và phần trả lời 3 câu "Cần hiểu".
  - Gỡ lỗi cài đặt môi trường (lỗi chạy `pip install` từ sai thư mục).
- **Tự kiểm tra:**
  - Chạy lại `python -m lab8.smoke` và `python -m pytest -q` trên máy mình, kết quả khớp với baseline trong CHECKPOINTS.md.
  - Đối chiếu nội dung do AI soạn với `docs/business_rules.md`, `docs/contracts.md` và code trong `src/lab8/`, rồi tự viết lại bằng lời của mình.
  - Soạn bản nháp `workflow.py`, `single.py` (CP2, CP3) và `src/tests/test_cp4_approval_secret.py` (CP4). Tôi đọc lại từng dòng, chạy test và giải thích được luồng của chúng.
  - Không dùng AI để sinh số liệu benchmark. Số liệu lấy từ lệnh chạy và file report.

## 6. Tự đánh giá

**CP1 — ba câu "Cần hiểu"**

1. **Vì sao tiền do `compute_compensation` tính, không do MockLLM?** Quote được tính từ dòng order và policy hiện hành bằng code xác định, nên cùng input thì cùng kết quả và kiểm tra lại được. MockLLM chỉ là mô phỏng có seed, sinh chữ và token giả, không có cơ chế bảo đảm số đúng. Ngoài ra host (`durability.issue_refund`) kiểm approval, trần theo đơn và idempotency rồi mới ghi ledger, nên model không có quyền quyết số tiền.

2. **Vì sao chữ trong ticket là dữ liệu người dùng?** Ticket do khách viết, có thể sai hoặc cố tình đưa lệnh (ví dụ "ignore policy", "trễ 9 ngày"). Ví dụ T02: ticket ghi 5 ngày, dòng order ghi 2 ngày. Nguồn sự thật là dòng order và policy có `is_current` và `effective_date <= as_of`, nên shape phải dùng số liệu từ đó, không lấy số ngày hay mã đơn từ câu chữ.

3. **`RunResult` có những `status` nào?**
   - `resolved`: đã ghi đúng một refund vào ledger (hoặc replay idempotent).
   - `needs_info`: thiếu `order_id`, không ghi ledger.
   - `escalated`: đơn không tìm thấy hoặc không thuộc principal, không trả thông tin nhạy cảm.
   - `denied`: quote bằng 0, hoặc host từ chối (approval hỏng, đơn đã hoàn đủ...), có audit `policy_denied` khi quote > 0.
   - `failed`: lỗi như claim không tồn tại, hoặc gọi lại với số tiền khác số đã commit (`amount_conflict`).

**CP2 — ba câu "Cần hiểu"**

1. **A, B, C, D khác nhau thế nào về mức tự chủ?** Cả bốn đều dùng chung quote và host, chỉ khác ai quyết định bước tiếp theo. A (workflow): code Python cố định thứ tự bước, model không quyết gì. B (single): một vòng ReAct, model chọn tool đọc tiếp theo, tối đa 8 bước. C (orchestrator): một agent điều phối giao việc cho các investigator chỉ đọc qua handoff. D (swarm): các agent tự chuyển việc cho nhau. Càng tự chủ thì càng linh hoạt nhưng càng tốn chi phí và càng khó đoán.

2. **Vì sao phải truyền quote đầy đủ vào `issue_refund` (T13, T14)?** Host mới là nơi biết đơn đã được hoàn bao nhiêu từ các claim trước, và tự trừ phần đó để giữ trần theo đơn. Nếu shape tự trừ rồi truyền số đã trừ, host trừ lần nữa nên khách nhận thiếu. Shape cũng có thể đọc lịch sử sai. Vì vậy shape chỉ đưa số tiền đầy đủ, `proposal_amount` giữ nguyên quote đầy đủ kể cả khi host từ chối.

3. **Vì sao shape tự từ chối thì không có audit `policy_denied`?** `policy_denied` do host ghi khi nó từ chối một yêu cầu hoàn tiền. Khi quote bằng 0, shape trả `denied` mà không gọi `issue_refund`, nên host không thấy gì và không có gì để ghi. Chỉ khi quote lớn hơn 0 và host từ chối (approval hỏng, đơn đã hoàn đủ) mới có đúng một audit `policy_denied`.

**CP3 — ba câu "Cần hiểu"**

1. **Vì sao checkpoint đơn lẻ không thay được ledger?** Checkpoint chỉ ghi "bước này đã xong", còn ledger ghi tiền đã đi. Nếu crash sau khi tiền đã ghi mà trước khi checkpoint, lần chạy lại chỉ nhìn checkpoint nên sẽ hoàn tiền lần hai. Ledger cùng audit `refund_committed` được ghi trong một transaction, và khi chạy lại host kiểm ledger trước. `lab8.demo.buggy_workflow` minh họa đúng lỗi này.

2. **Idempotency key `refund:{claim_id}` để làm gì?** Mỗi claim chỉ có một khóa hoàn tiền. Gọi lại cùng claim với cùng số tiền thì host trả lại kết quả cũ (replay), không ghi dòng mới, nên crash rồi resume vẫn chỉ có một refund. Gọi lại với số tiền khác thì host báo `amount_conflict`, shape trả `failed`.

3. **Vì sao tóm tắt bằng LLM không tính là redaction?** LLM không bảo đảm bỏ hết dữ liệu nhạy cảm, có thể giữ lại số điện thoại hay địa chỉ dưới dạng diễn đạt khác, và kết quả không kiểm chứng được. Redaction phải là code xác định như allowlist trong `handoff.py`: chỉ field được liệt kê mới đi qua, phần còn lại bị bỏ.

**CP4 — ba câu "Cần hiểu"**

1. **Cổng duyệt của host chặn gì?** Host kiểm approval của chính claim đó trước khi ghi ledger. Nó chặn: thiếu approval, approval của claim khác, approval đã thu hồi hoặc hết hạn, số tiền duyệt bằng 0 hoặc thấp hơn quote, và đơn đã được hoàn đủ theo trần. Mỗi lần chặn host ghi một audit `policy_denied` với lý do, và không ghi dòng ledger nào. Tôi kiểm lại bằng 6 ca hỏng trong `test_broken_approval_never_writes_a_refund`.

2. **Vì sao trace là ranh giới bảo mật chứ không phải tiện ích debug?** Trace là file shape xuất ra ngoài. Nếu ghi claim row hay order row thô thì số điện thoại, địa chỉ, ghi chú nội bộ và secret sẽ rò ra khỏi hệ thống. Vì vậy trace chỉ ghi các sự kiện đã chọn lọc. `test_no_secret_or_personal_data_leaves_the_shape` quét kết quả, file trace và stdout của 14 claim để bảo đảm điều đó.

3. **Vì sao grader fail-closed?** Khi trace thiếu (`missing_trace`), cũ (`stale_trace`), sai định dạng (`invalid_trace`) hoặc sai `run_id` (`trace_run_id_mismatch`), grader coi trial là fail thay vì bỏ qua. Nếu không, shape có thể tắt trace để giấu rò rỉ và vẫn qua. Vì vậy mọi nhánh return, kể cả `needs_info` và `escalated`, đều phải ghi trace hợp lệ.
