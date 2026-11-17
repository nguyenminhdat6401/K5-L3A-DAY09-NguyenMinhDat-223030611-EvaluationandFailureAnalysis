# Provenance audit — v1

Kiểm tra tự động từ item, nhãn gốc Lab 8 và report fixed đã sinh bằng harness.
Nhãn v1 trùng hoàn toàn expected trong nguồn public; không có nhãn inline trong item.
Report kiểm chứng: `E-fixed-20261117-4940`, spec `1.1`.

| Item | Claim | Kiểm chứng nhãn | Replay fixed | Review trace thủ công |
|---|---|---|---|---|
| E-001 | C-001 | Khớp nguồn | 5/5 PASS | Có, theo provenance |
| E-002 | C-002 | Khớp nguồn | 5/5 PASS | Có, theo provenance |
| E-003 | C-003 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-004 | C-004 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-005 | C-005 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-006 | C-006 | Khớp nguồn | 5/5 PASS | Có, theo provenance |
| E-007 | C-007 | Khớp nguồn | 5/5 PASS | Có, theo provenance |
| E-008 | C-008 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-009 | C-009 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-010 | C-010 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-011 | C-011 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-012 | C-012 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-013 | C-013 | Khớp nguồn | 5/5 PASS | Chưa; chỉ có replay tự động |
| E-014 | C-014 | Khớp nguồn | 5/5 PASS | Có, theo provenance |

Reviewer tự động không thay thế review trace thủ công hoặc đáp án 5 anchor.
Chưa được cung cấp danh sách/key anchor riêng của giảng viên; chưa tuyên bố đối chiếu thành công.
Không thay checked_by thành tên người cho các item chưa được review thủ công.
Các mã failure_modes là coverage được đề xuất; không có nghĩa mọi mode đã xảy ra ở baseline.
