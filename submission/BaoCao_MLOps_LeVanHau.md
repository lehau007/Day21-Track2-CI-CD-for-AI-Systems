# Báo Cáo Thực Hành MLOps: Từ Thực Nghiệm Cục Bộ Đến Triển Khai Liên Tục

**Môn học:** AIInAction - VinUni  
**Buổi:** Day 21 - CI/CD cho AI Systems

---

## 1. Lựa Chọn Siêu Tham Số (Hyperparameters) - Kết Quả Bước 1

Trong quá trình thực nghiệm ở Bước 1 bằng MLflow, em đã thử nghiệm nhiều bộ cấu hình khác nhau cho thuật toán `RandomForestClassifier`. Sau khi so sánh độ đo `accuracy` và `f1_score` trên MLflow UI, bộ siêu tham số tốt nhất được chọn để đưa vào triển khai là:

- **n_estimators**: 300
- **max_depth**: 20
- **min_samples_split**: 2

**Lý do lựa chọn:** Số lượng cây quyết định (n_estimators) lớn kết hợp với độ sâu vừa đủ (max_depth=20) giúp mô hình học được các pattern phức tạp của tập dữ liệu Wine Quality mà không bị overfitting quá mức, giữ vững độ cân bằng tốt cho F1-Score so với các bộ tham số mặc định.

---

## 2. Các Khó Khăn Gặp Phải Và Cách Giải Quyết

Trong quá trình xây dựng hệ thống CI/CD và triển khai API, em đã đối mặt và giải quyết thành công một số bài toán thực tế sau:

### 2.1. Lỗi Timeout Khi Gọi API Tới AWS EC2
- **Vấn đề:** Không thể truy cập API bằng lệnh `curl http://<IP>:8000/health`, kết nối liên tục bị treo và văng lỗi Time out sau 21 giây.
- **Cách giải quyết:** Lỗi này do tường lửa bên ngoài (AWS Security Group) đang chặn truy cập. Em đã vào giao diện AWS Management Console, chỉnh sửa Inbound Rules của Security Group gắn với EC2, thêm rule `Custom TCP` cho Port `8000` với Source `0.0.0.0/0`. Ngay lập tức kết nối thành công.

### 2.2. Lỗi Quyền Truy Cập Khi Đổi Port (Permission Denied)
- **Vấn đề:** Khi thử đổi cổng dịch vụ API từ 8000 sang cổng HTTP tiêu chuẩn 80, systemd service báo lỗi sập ngang do ứng dụng chạy dưới quyền user bình thường (`ubuntu`), không đủ đặc quyền.
- **Cách giải quyết:** Theo thiết kế bảo mật của Linux, các cổng < 1024 yêu cầu quyền `root`. Em đã chọn phương pháp linh hoạt hơn là giữ nguyên port `8000` để chạy ứng dụng an toàn mà không cần cấp quyền root nguy hiểm cho tiến trình Python, sau đó đổi cấu hình GitHub Actions khớp về port 8000.

### 2.3. Lỗi Parser Chuỗi JSON Trong Windows PowerShell
- **Vấn đề:** Khi dùng lệnh `curl` với `-d '{"features": [...]}'` trong PowerShell, API trả về lỗi `JSON decode error` do PowerShell "ăn" mất các dấu ngoặc kép.
- **Cách giải quyết:** Thay thế lệnh `curl.exe` bằng lệnh native chuyên dụng của Windows là `Invoke-RestMethod` cùng cấu trúc `-Body` và `-Headers` chuẩn xác. Kết quả gọi dự đoán trả về chuẩn `{"prediction": 0, "label": "thap"}`.

### 2.4. GitHub Actions Không Kích Hoạt Tự Động (Bước 3)
- **Vấn đề:** Ở pha Huấn luyện liên tục, sau khi chạy `add_new_data.py` và push code lên GitHub, Pipeline không tự động chạy.
- **Cách giải quyết:** Nguyên nhân do trong commit em quên chưa chạy lệnh `dvc add` để cập nhật con trỏ `.dvc`. Cấu hình `mlops.yml` chỉ trigger khi file `.dvc` có biến đổi. Giải pháp là chạy đúng flow: `dvc add data/train_phase1.csv` -> `dvc push` -> commit file `train_phase1.csv.dvc` mới -> `git push`. Pipeline đã nhận diện đúng sự thay đổi dữ liệu và tiến hành tự động đào tạo lại xuất sắc.

---
*Báo cáo kết thúc.*
