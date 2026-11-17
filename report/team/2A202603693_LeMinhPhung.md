# Báo cáo cá nhân — Lê Minh Phụng

## 1. Thông tin thành viên

- Họ tên: Lê Minh Phụng
- MSSV: 2A202603693
- Email: 26ai.phunglm@vinuni.edu.vn
- GitHub: okuminhphen

## 2. Phần việc phụ trách

Phụ trách shape `orchestrator`, handoff cho investigator, kiểm tra trace và các tình huống gọi lại hoặc tiếp tục sau crash.

## 3. Đóng góp cụ thể

- Commit `b86baa3` bổ sung `run_claim` trong [orchestrator.py](../../src/lab8/shapes/orchestrator.py) và test `test_orchestrator_traces_a_read_only_handoff` trong [test_orchestrator_handoff.py](../../src/tests/test_orchestrator_handoff.py).
- Orchestrator dùng `make_handoff` để giao hai tool đọc là `lookup_order` và `compute_compensation`. Investigator tra đơn và tính tiền theo policy. Orchestrator chuyển nguyên quote cho `issue_refund` để host áp dụng approval và trừ khoản đã hoàn trước đó.
- Trace ghi handoff đã lọc, quyền xem đơn, số tiền đề xuất và trạng thái. `finish()` ghi trace và lấy khoản hoàn thực tế từ ledger.

- Bonus B2 (gắn nhãn lỗi MAST): thêm `src/tests/test_bonus_mast_rules.py` với hai test kiểm luật của tagger trên event dựng tay phía handoff và trace: `test_handoff_that_matches_the_order_row_is_not_misalignment` (handoff khớp dòng order thì không bị gán lỗi FC2) và `test_override_event_is_verification_failure_and_missing_trace_is_system_design` (event `model_override` là FC3, thiếu trace là FC1).

## 4. Bằng chứng

- Bộ test public của orchestrator đạt **62/62**, gồm T11 kiểm tra gọi lại và T12 kiểm tra tiếp tục sau crash. Bộ test mặc định đạt **55/55** sau khi thêm test handoff.
- Test handoff dùng claim `C-001`, seed `11`. Test kiểm tra mã lần chạy trong trace, hai tool được cấp cho investigator và sự vắng mặt của `CANARY_SECRET_` trong trace và đầu ra terminal.
- Báo cáo [crash.json](../../src/reports/crash.json) ghi `crash_safety: 20/20` cho bộ kiểm tra host và swarm tham chiếu. T12 trong bộ public là bằng chứng crash riêng của orchestrator.
- Kiểm tra CP4 trên 14 claim public với 5 seed cho **70/70 lượt sạch** theo các chuỗi cấm của fixture và các trường `ticket`, `parent_secret`, `raw_headers` trong trace, stdout và stderr. Bộ test host về quyền truy cập, approval và trần theo đơn đạt **11/11**.

## 5. Công cụ AI đã dùng

Tôi dùng Codex để giải thích input/output của `run_claim`, triển khai orchestrator và bổ sung test handoff. Tôi dùng kết quả kiểm thử do Codex chạy trên repo cục bộ làm bằng chứng. Bộ public kiểm tra các trạng thái trả về, số tiền hoàn và hành vi khi chạy lại sau crash. Test handoff đọc file tại `result.trace_path` để đối chiếu quyền của investigator và kiểm tra dấu hiệu lộ secret.

## 6. Tự đánh giá

Tôi dựa vào Codex cho phần triển khai và thêm test. Một ví dụ tôi có thể dùng để giải thích luồng xử lý là T14. Investigator tính quote 150.000đ, orchestrator chuyển nguyên quote cho host, rồi host trừ 30.000đ đã hoàn và ghi thêm 120.000đ. `RunResult.proposal_amount` vì thế vẫn là 150.000đ.

Bước tôi cần tự thực hành là chạy lại T12 và đọc kết quả để chỉ ra vì sao lần chạy lại sau crash vẫn chỉ có một khoản hoàn. Với trace, tôi sẽ mở một lần chạy của `C-001` và đối chiếu hai tool trong handoff với phần quyền của investigator trong code.
