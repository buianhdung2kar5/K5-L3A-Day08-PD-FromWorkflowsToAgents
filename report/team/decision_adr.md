# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 6f5f8ad
- Run id dẫn chứng: R-workflow-C-001-s11 (70/70 trial của workflow trong src/reports/benchmark.json, seed 11,22,33,44,55)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000-1.000 / 0.000000 (70 trial, bộ public 14 claim × 5 seed)
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (src/reports/crash.json; chạy trên host và swarm tham chiếu). T12 crash rồi resume qua 62/62 test student của workflow
- Secret leak / approval bypass: 0 / 0 (benchmark không có trial nào bị đánh dấu leak_suspect; test_cp4_approval_secret.py: 6 ca approval hỏng và quét secret trên 14 claim × 2 seed đều xanh)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên cùng corpus 14 claim và cùng 5 seed (70 trial mỗi shape), workflow và single đều đạt pass rate 1.000, pass^5 1.000 và variance 0. Orchestrator cũng đạt 1.000 nhưng cost/success 43.57. Swarm đạt 0.986, pass^5 0.929, cost/success 49.57, và fail một trial duy nhất: C-002 ở seed 55 (`resolved` thay vì `denied`). Workflow có cost/success thấp nhất (27.86, bằng single), không gọi model nào (mean_model_calls 0), và thứ tự bước cố định nên dễ chứng minh tiền chỉ do `compute_compensation` quyết định và chỉ host ghi ledger. Ta chọn workflow vì nó đạt cùng độ chính xác với chi phí thấp nhất và ít bề mặt lỗi nhất. Nguồn số liệu: `src/reports/benchmark.json`.

## Có đáng đổi lấy multi-agent không

Nếu pass nhỉnh hơn mà cost và variance cao hơn, nhóm giữ hay đổi? Điều kiện nào làm quyết định đảo lại?

Ở bộ public không có shape multi-agent nào pass cao hơn workflow: orchestrator bằng (1.000) với cost cao hơn khoảng 56%, swarm thấp hơn (0.986) và có variance. Vậy không có lý do đổi. Quyết định chỉ đảo lại khi có đủ cả ba điều kiện: (1) trên bộ hidden hoặc corpus lớn hơn workflow rớt dưới ngưỡng 0.75 hoặc thấp hơn rõ rệt một shape khác với cùng seed; (2) phần fail do các nhánh mà quy tắc cố định không phủ được (ví dụ ticket có tình huống mới cần suy luận); (3) mức tăng pass rate lớn hơn mức tăng cost/success và variance. Với claim còn tuần tự và quy tắc rõ như hiện nay, thêm investigator chỉ tăng chi phí.

## Trace và bằng chứng

Trace của nhóm ghi những event nào? Field nào cố ý **không** ghi, và vì sao? Nếu trace nằm ngoài chỗ scanner quét được, đội security chứng minh thế nào là hệ thống không lộ secret?

Workflow ghi các event: `claim` (chỉ có `found`), `order` (`visible`, `reason`), `quote` (`amount_vnd`, `reason`), `host` (`ok`, `reason`, `conflict`) và `decision`. Trace không ghi claim row hay order row thô, nên không có phone, address, internal note, tên món, `parent_secret` hay `raw_headers`, vì đây là dữ liệu cá nhân hoặc secret và trace là ranh giới bảo mật. Trace được ghi bằng `lab8.trace.Trace` cho mọi nhánh return. Bằng chứng: `test_no_secret_or_personal_data_leaves_the_shape` quét kết quả, file trace và stdout của 14 claim × 2 seed, và benchmark không có trial nào bị đánh dấu `leak_suspect`.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75. Workflow không dùng model nên pass 1.000 ở đây không cho biết nó xử lý ticket tự do tốt đến đâu. Corpus public chỉ có 14 claim; cost là VND mô phỏng, không phải hóa đơn API. Crash suite 20/20 chạy trên host và swarm tham chiếu, bằng chứng crash riêng của workflow là T12.
