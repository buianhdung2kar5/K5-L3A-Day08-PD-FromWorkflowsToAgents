# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri và cộng sự, *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025, arXiv:2503.13657 (https://arxiv.org/abs/2503.13657). Bằng chứng: phân tích thực nghiệm các trace của nhiều framework multi-agent. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lỗi của hệ multi-agent có thể phân thành các nhóm: lỗi đặc tả và thiết kế, lệch pha giữa các agent, và lỗi kiểm chứng/kết thúc tác vụ. Phần lớn lỗi không đến từ năng lực của từng model mà từ cách hệ thống tổ chức và kiểm chứng. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận của paper dựa trên các framework và tác vụ cụ thể với model thật. Lab này dùng MockLLM, 14 claim và một lỗi duy nhất của swarm, nên chỉ minh họa cách phân loại, không kiểm chứng lại tỷ lệ các nhóm lỗi của paper. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Lỗi của swarm ở C-002 seed 55 thuộc nhóm lỗi kiểm chứng: swarm nhận số ngày trễ trong ticket (5) thay vì số trong dòng order (2) mà không đối chiếu lại. Nếu đổi từ swarm sang workflow, nơi số ngày chỉ lấy từ dòng order, thì pass rate trên cùng 70 trial tăng từ 0.986 lên 1.000, pass^5 từ 0.929 lên 1.000, variance giữa các seed về 0 và cost/success giảm từ khoảng 49.57 xuống khoảng 27.86. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định: MockLLM, các tool, 14 claim public, seed 11,22,33,44,55, bảng giá mô phỏng, grader. Biến duy nhất được thay đổi: shape (swarm so với workflow). Đọc event `model_override` trong trace `R-swarm-C-002-s55` để xác định nhóm lỗi. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: swarm tin số ngày trong ticket khi `seed % 5 == 0`, quote 20.000 và trả `resolved` thay vì `denied` ở T02. Đo bằng pass rate, pass^5, variance theo seed, số trial `status resolved != denied`, và `refund_count` trong ledger. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json`; trial fail duy nhất: `R-swarm-C-002-s55`; trial đối chứng: `R-workflow-C-002-s55`
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng.** Swarm pass 69/70 (0.986), pass^5 0.929, seed 55 chỉ đạt 0.929 còn các seed khác 1.000, variance 0.000816. Workflow pass 70/70, pass^5 1.000, variance 0, cost/success 27.86 so với 49.57 của swarm. Trace swarm có event `model_override` đặt `delay_days` = 5 trong khi dòng order ghi 2, nên quote 20.000 thay vì 0. Lỗi này thuộc nhóm kiểm chứng (không đối chiếu với nguồn sự thật). Giới hạn: chỉ một trial fail trên 14 claim, nên đây là một ví dụ và không phải thống kê.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
