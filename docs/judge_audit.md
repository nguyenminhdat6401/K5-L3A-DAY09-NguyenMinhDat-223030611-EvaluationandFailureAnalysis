# Judge audit

Các lệnh chạy trong src:

    python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5
    python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5

FAIL là lớp dương: judge có nhiệm vụ phát hiện lỗi.

## Kết quả calibration

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS? | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có | Dùng cho đánh giá tone trong phạm vi đã kiểm chứng |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không | Không dùng làm gate |

Ngưỡng: κ ≥ 0.6, precision ≥ 0.8, recall ≥ 0.7.

## Audit bất đồng

Đối chiếu reply, nhãn và ghi chú trong CSV công khai.
Cột nhận định dưới đây dựa trên rubric/ngữ cảnh được cung cấp,
không phải một bộ nhãn độc lập mới.

| Case | Judge | Người | Nhận định | Hành động sửa rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Đồng ý nhãn người theo note: cách xưng hô và “nha” quá suồng sã trong ngữ cảnh này. | Bổ sung ví dụ ranh giới giữa thân thiện và suồng sã; không chỉ dựa vào từ lịch sự. |
| H-017 | PASS | FAIL | Theo note, cách gọi “bạn” không phù hợp khách lớn tuổi. Reply riêng lẻ không đủ chứng minh tuổi khách. | Cung cấp ngữ cảnh xưng hô; nếu thiếu thì yêu cầu review thay vì suy đoán. |
| H-029 | PASS | FAIL | “Không cần nhắn thêm” mang tính áp đặt dù mở đầu có “Dạ, vui lòng”. | Chấm toàn câu, bổ sung ví dụ giọng ra lệnh hoặc ngăn khách phản hồi. |
| H-042 | FAIL | PASS | Đồng ý nhãn người: câu ngắn, lịch sự và có thời gian dự kiến; thiếu xin lỗi không tự động là tone xấu. | Không bắt buộc lời xin lỗi trong mọi câu trả lời. |
| H-051 | FAIL | PASS | Theo note, thuật ngữ “refund” được CS LogiX cho phép. | Thêm danh sách thuật ngữ được phép, tránh phạt chỉ vì có tiếng Anh. |
| HL-015 | PASS | FAIL | Reply nói 55.000đ, note ghi ledger 40.000đ. | Tách kiểm tra tiền khỏi tone; đối chiếu ledger bằng code. |
| HL-016 | PASS | FAIL | Lời xin lỗi dài không khắc phục việc báo 55.000đ trong khi note ghi ledger 35.000đ. | Không cộng điểm nội dung đúng chỉ vì văn phong lịch sự hoặc dài. |
| HL-020 | PASS | FAIL | Reply nói 90.000đ, note ghi ledger 120.000đ. | Kiểm tra số tiền được khẳng định đã hoàn với effect thực tế. |
| HL-028 | PASS | FAIL | Reply nói 50.000đ, note ghi ledger 35.000đ. | Xem sai tiền là lỗi bắt buộc fail, độc lập với lời xin lỗi. |
| HL-035 | PASS | FAIL | Reply nói 50.000đ, note ghi ledger 35.000đ. | Dùng grader code cho tính nhất quán reply–ledger. |

## Ma trận nhầm lẫn

Tone: TP=24, FP=4, FN=6, TN=66.
Helpful: TP=9, FP=0, FN=21, TN=70.

Tone vẫn bỏ sót 6 lỗi và báo nhầm 4 trường hợp.
Helpful chỉ phát hiện 9/30 lỗi nên không đủ tin cậy làm gate.

## Hiệu chỉnh tỷ lệ lỗi

- Tone: observed failure rate 0.28; Rogan–Gladen corrected 0.30.
- Helpful: observed failure rate 0.09; corrected 0.30.

Hiệu chỉnh là ước lượng tỷ lệ tổng thể theo sensitivity/specificity,
không sửa từng verdict và không khiến helpful đạt calibration.

## Kết luận và giới hạn

Tone đạt các ngưỡng trên dữ liệu replay công khai.
Helpful bị loại khỏi gate vì κ và recall dưới ngưỡng.

Tiền, approval và ledger phải được kiểm tra bằng code.
Không dùng độ lịch sự làm bằng chứng rằng refund đúng.

Các hành động sửa rubric trên là đề xuất, chưa được kiểm chứng
bằng một lần chạy judge mới. Cần dữ liệu do người gán nhãn mới
và held-out độc lập để đánh giá lại, tránh tối ưu theo bộ public.