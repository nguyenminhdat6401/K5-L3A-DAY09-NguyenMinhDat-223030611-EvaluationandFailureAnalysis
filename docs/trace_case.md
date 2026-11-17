# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | seeded_regression C-002@11 |
| Triệu chứng | Lab 8 grader FAIL: status resolved != denied. Ledger ghi một refund 20.000đ, nhãn yêu cầu không refund. |
| Bước sai đầu tiên | Event 3: model_override, payload {"delay_days": 5}. Agent dùng delay từ ticket để ghi đè dữ liệu order. |
| Vì sao là bước đầu tiên | Event 1 tạo handoff; event 2 đọc order thành công. Event 3 là bước thay đổi dữ kiện trước khi event 4 tính quote sai thành 20.000đ. |
| Failure mode | FM-03 — ticket_trust |
| Đối chứng | fixed C-002@11 PASS; không có model_override. Event 3 quote bằng 0, ledger không có refund và status denied. |
| Regression test | tests/test_lab9_ticket_trust_case.py::test_lab9_ticket_trust_c002 — 2 passed. Evaluator chấp nhận fixed và phát hiện seeded_regression qua ledger/status sai nhãn. |
| Chưa chắc chắn | Một trace chưa chứng minh hành vi trên claim hoặc seed khác. Trace không cho phép suy ra suy nghĩ nội bộ của model. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
