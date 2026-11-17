# Team

## Thông tin nhóm

- Tên nhóm:PD
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-PD-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/buianhdung2kar5/K5-L3A-Day08-PD-FromWorkflowsToAgents, nhánh `main`, commit `7b97e57`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Bùi Anh Dũng | 2A202603687 | <26ai.dungba2@vinuni.edu.vn> | <https://github.com/buianhdung2kar5> | Workflow, single, test CP4, benchmark, ADR |
|   2 | Lê Minh Phụng | 2A202603693 | 26ai.phunglm@vinuni.edu.vn | okuminhphen | Orchestrator, Handoff, kiểm thử crash/resume và rà soát trace |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Bùi Anh Dũng | Workflow, single, test CP4, bonus B2 | `6bc174c` | `test_broken_approval_never_writes_a_refund` (6 ca approval hỏng × workflow/single), `test_no_secret_or_personal_data_leaves_the_shape` (14 claim × seed 11, 55 × workflow/single); bonus B2 trong `src/tests/test_bonus_mast.py`: `test_each_variant_fails_somewhere_and_is_tagged_with_its_group` (3 variant), `test_a_correct_run_is_not_tagged`, `test_override_event_is_verification_failure_and_missing_trace_is_system_design`, `test_handoff_that_matches_the_order_row_is_not_misalignment`, `test_cohens_kappa_known_values` |
| Lê Minh Phụng | Orchestrator, Handoff, kiểm thử crash/resume và rà soát trace | `b86baa3` | `test_orchestrator_traces_a_read_only_handoff` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## Bùi Anh Dũng (2A202603687)

### Phần việc phụ trách

Workflow, single, test approval hỏng và rò rỉ secret (CP4), benchmark, ADR, research card, báo cáo nhóm.

### Đóng góp cụ thể

Viết `workflow.py` và `single.py`, truyền `crash_at` vào host, thêm `src/tests/test_cp4_approval_secret.py`, sinh `crash.json` và `benchmark.json`, gộp nhánh orchestrator.

### Bằng chứng

Commit `c9bc306`, `cf0071e`, `6bc174c`, `537db2e`, `7b97e57`; báo cáo `report/team/2A202603687_BuiAnhDung.md`.

## Lê Minh Phụng (2A202603693)

### Phần việc phụ trách

Orchestrator, handoff, kiểm thử crash/resume và rà soát trace.

### Đóng góp cụ thể

Viết `orchestrator.py` với handoff chỉ đọc và test `test_orchestrator_traces_a_read_only_handoff`.

### Bằng chứng

Commit `b86baa3`; báo cáo `report/team/2A202603693_LeMinhPhung.md`.
