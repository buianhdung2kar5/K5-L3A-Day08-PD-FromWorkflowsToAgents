# Bonus report: B2

- Topic + nguồn (tên, năm, slide): B2, gắn nhãn lỗi theo MAST. Cemri và cộng sự, *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025 (slide 35, 45).
- CLAIM của nguồn (1 câu): lỗi của hệ multi-agent chia thành 3 nhóm (system design, inter-agent misalignment, task verification), và taxonomy này gán nhãn được cho các trace với độ đồng thuận cao giữa người gán nhãn.
- BOUNDARY (model / dataset / setup): paper dùng trace của các framework multi-agent thật với model thật. Ở đây chỉ có MockLLM, 14 claim public, một lỗi thật của swarm và ba lỗi do nhóm chèn có chủ đích, nên không kiểm lại tỷ lệ các nhóm lỗi của paper.
- HYPOTHESIS trên LogiX: một tagger bằng luật đọc event trong trace (không đọc tên shape) gán đúng nhóm MAST cho lỗi của một shape multi-agent, và lỗi swarm ở seed 55 thuộc nhóm task verification.
- Biến cố định / biến thay đổi: cố định MockLLM, tool, host, 14 claim, seed `11,22,33,44,55`, bảng giá, evaluator. Biến thay đổi: loại lỗi được chèn vào (3 variant) và shape swarm tham chiếu.
- Lệnh tái lập (copy-paste được), chạy trong `src/`:

```bash
python -m lab8.benchmark --shapes workflow,swarm,handoff_drops_delay,stale_policy,ignores_host_result --extra-shape handoff_drops_delay=bonus.broken_shapes:handoff_drops_delay --extra-shape stale_policy=bonus.broken_shapes:stale_policy --extra-shape ignores_host_result=bonus.broken_shapes:ignores_host_result --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json
python -m bonus.make_labels
python -m bonus.mast_tag
python -m pytest -q tests/test_bonus_mast.py
```

- File report + run id: `src/reports/bonus_benchmark.json`, `src/reports/bonus_mast.json`; nhãn `src/bonus/labels.json`; lỗi swarm thật: `R-swarm-C-002-s55`.

## Kết quả

Ba variant trong `src/bonus/broken_shapes.py` sao chép flow của workflow và chèn đúng một lỗi. Host vẫn là writer duy nhất nên không variant nào qua mặt được approval hay trần theo đơn.

| Shape | Lỗi chèn vào | Pass rate | pass^5 | Cost/success (VND mô phỏng) |
| --- | --- | --: | --: | --: |
| workflow | không | 1.000 | 1.000 | 27.86 |
| swarm | tin số ngày trong ticket (seed 55) | 0.986 | 0.929 | 49.57 |
| handoff_drops_delay | handoff làm rơi `delay_days` | 0.500 | 0.500 | 55.71 |
| stale_policy | quote đọc cả policy đã bị thay thế | 0.214 | 0.214 | 90.00 |
| ignores_host_result | báo `resolved` dù host từ chối | 0.857 | 0.857 | 32.50 |

Tagger gán nhãn 101 trial fail (70 trial mỗi shape):

| Shape | FC1 system design | FC2 inter-agent | FC3 verification |
| --- | --: | --: | --: |
| handoff_drops_delay | 0 | 35 | 0 |
| stale_policy | 55 | 0 | 0 |
| ignores_host_result | 0 | 0 | 10 |
| swarm | 0 | 0 | 1 |

- **Độ khớp với nhãn:** accuracy 1.000, Cohen's κ 1.000 trên 101 trial.
- **Độ đặc hiệu:** 0/70 trial của workflow bị gán nhầm.
- **Lỗi tiềm ẩn:** có 55 trial của ba variant vẫn pass nhưng mang dấu hiệu lỗi (handoff 30, stale_policy 15, ignores_host_result 10). Lỗi có mặt nhưng không làm sai kết quả của claim đó.
- **Safety counts** (từ `bonus_benchmark.json`, 5 shape × 70 trial): 0 trial bị đánh dấu `leak_suspect`. Không có variant nào ghi được refund khi host từ chối: ledger vẫn do host ghi, nên `ignores_host_result` chỉ sai ở status báo cáo (10 trial `resolved` thay vì `denied`).
- **Test:** 7 test. `src/tests/test_bonus_mast.py` (5 test, do Dũng): chạy từng variant thật rồi kiểm nhóm tagger gán, kiểm run đúng không bị gán nhãn, và κ. `src/tests/test_bonus_mast_rules.py` (2 test, do Phụng): luật của tagger trên event dựng tay, gồm handoff khớp order row và event `model_override`.

## Kết luận

**Ủng hộ một phần.** Lỗi swarm ở `R-swarm-C-002-s55` được gán vào **FC3 (task verification)**: trace có event `model_override` đặt `delay_days` = 5 trong khi dòng order ghi 2, và không có bước nào đối chiếu giá trị đó với order. Biện pháp phù hợp với nhóm lỗi này là thêm một bước kiểm bằng code so mọi dữ kiện dùng để quote với dữ liệu có cấu trúc, đúng như workflow đang làm (số ngày chỉ lấy từ dòng order). Tagger bằng luật phân biệt được ba loại lỗi chèn vào chỉ dựa trên event trong trace.

Điều chưa được chứng minh:
- **Nhãn không độc lập.** Nhãn trong `labels.json` suy ra từ lỗi được chèn vào mỗi variant, không phải từ người gán nhãn độc lập. Các luật của tagger cũng do chính nhóm viết sau khi biết các lỗi. Vì vậy κ = 1.000 chỉ cho thấy luật nhất quán với lỗi đã biết, không chứng minh tagger gán đúng cho lỗi lạ.
- **Chỉ một lỗi thật.** Trong 14 claim chỉ có đúng một trial fail tự nhiên (swarm, seed 55).

Kết luận đảo ngược khi: (1) hai người gán nhãn độc lập trên các trial fail thật cho κ thấp, hoặc không khớp tagger; (2) một lỗi thật có hai dấu hiệu cùng lúc (ví dụ policy cũ và handoff rơi dữ kiện) làm thứ tự luật quyết định kết quả, vì tagger chỉ gán một nhóm và luật đầu tiên khớp thắng; (3) trace của shape khác không ghi các event mà luật dựa vào, khi đó tagger trả `unclassified`.

## Giới hạn

- MockLLM không phải model sản xuất. Lỗi của model thật thường mơ hồ hơn nhiều so với ba lỗi cố ý chèn.
- Latency không đo; cost là VND mô phỏng.
- Taxonomy MAST của paper có nhiều failure mode hơn; tagger chỉ dùng 3 nhóm và 5 mode (information withholding, disobey task specification, incorrect verification, no or incomplete verification, và không phân loại được). Tên mode viết theo cách nhóm hiểu paper.
- Luật dựa vào tên event (`model_override`, `handoff`, `order`, `policy_used`, `host`), nên chỉ áp dụng được cho shape ghi các event này.
- Bonus chỉ được tính khi workflow qua đủ must-pass và pass rate hidden ≥ 0.80; điều này do giảng viên chấm.
