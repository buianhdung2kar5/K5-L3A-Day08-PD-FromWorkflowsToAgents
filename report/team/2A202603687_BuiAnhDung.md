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
  - Không dùng AI để viết code shape hay sinh số liệu benchmark. Các phần đó tôi tự làm và kiểm tra bằng test và lệnh chạy.

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
