# AGENTS.md - Hướng Dẫn Cho Agent Day 21

Tài liệu này dành cho agent để hiểu cấu trúc dự án, luồng thực thi, và nhận biết rõ khi nào cần người dùng hỗ trợ. Mục tiêu là bám đúng từng bước, biết file nào là trung tâm của mỗi giai đoạn, và biết lúc nào cần nhắc người dùng chụp màn hình hoặc cung cấp thông tin ngoài repo.

## 1. Kiến Trúc Thư Mục

### 1.1 Cấu trúc hiện có trong repo

```text
Day21-Track2-CI-CD-for-AI-Systems/
├── add_new_data.py
├── generate_data.py
├── params.yaml
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── serve.py
│   └── train.py
├── tasks/
│   ├── buoc-1.md
│   ├── buoc-2.md
│   └── buoc-3.md
└── tests/
    ├── __init__.py
    └── test_train.py
```

### 1.2 Cấu trúc đích sau khi hoàn thành lab

```text
Day21-Track2-CI-CD-for-AI-Systems/
├── .github/
│   └── workflows/
│       └── mlops.yml
├── .dvc/
│   └── config
├── data/
│   ├── train_phase1.csv.dvc
│   ├── eval.csv.dvc
│   └── train_phase2.csv.dvc
├── src/
│   ├── __init__.py
│   ├── train.py
│   └── serve.py
├── tests/
│   ├── __init__.py
│   └── test_train.py
├── generate_data.py
├── add_new_data.py
├── params.yaml
├── requirements.txt
├── README.md
└── AGENTS.md
```

### 1.3 Ý nghĩa các phần chính

- `generate_data.py`: tạo và chia dữ liệu ban đầu.
- `add_new_data.py`: ghép dữ liệu mới để mô phỏng huấn luyện liên tục.
- `params.yaml`: nơi chỉnh siêu tham số cho mô hình.
- `src/train.py`: huấn luyện cục bộ, ghi MLflow, xuất `outputs/metrics.json` và `models/model.pkl`.
- `src/serve.py`: API suy luận chạy trên VM, tải model từ object storage.
- `tests/test_train.py`: unit test cho phần huấn luyện.
- `tasks/`: mô tả từng bước của lab, dùng làm checklist thực hiện.

## 2. Công Việc Cần Làm Theo Từng Bước

### Bước 1 - Thực nghiệm cục bộ và theo dõi thí nghiệm

Mục tiêu: chạy ít nhất 3 lần huấn luyện với siêu tham số khác nhau, ghi nhận `accuracy` và `f1_score` trong MLflow, rồi chọn bộ siêu tham số tốt nhất.

Checklist:

1. Chạy `python generate_data.py` để tạo dữ liệu.
2. Cài thư viện từ `requirements.txt`.
3. Cấu hình MLflow local với SQLite backend.
4. Hoàn thiện `src/train.py` để:
   - đọc `data/train_phase1.csv` và `data/eval.csv`
   - train `RandomForestClassifier`
   - log params và metrics lên MLflow
   - lưu `outputs/metrics.json`
   - lưu `models/model.pkl`
5. Chạy ít nhất 3 thí nghiệm bằng cách thay đổi `params.yaml`.
6. Mở MLflow UI, so sánh kết quả và chọn bộ siêu tham số tốt nhất.
7. Cập nhật `params.yaml` theo bộ tốt nhất trước khi sang bước sau.

Điểm cần nhắc người dùng chụp screenshot làm bằng chứng:

- MLflow UI hiển thị ít nhất 3 runs.
- Màn hình compare hoặc sort runs theo `accuracy`.
- Bằng chứng `outputs/metrics.json` và `models/model.pkl` tồn tại nếu cần đối chiếu nhanh.

### Bước 2 - Pipeline CI/CD tự động

Mục tiêu: mỗi lần push code hoặc thay đổi dữ liệu `.dvc`, GitHub Actions tự test, train, kiểm tra ngưỡng `accuracy >= 0.70`, và deploy lên VM nếu đạt.

Checklist:

1. Tạo bucket object storage trên cloud provider đã chọn.
2. Tạo credentials phù hợp và không commit secret vào git.
3. Khởi tạo DVC, cấu hình remote, rồi `dvc add` cho các file dữ liệu.
4. Commit các file `.dvc` và `.dvc/config`, sau đó `dvc push`.
5. Tạo VM trên cloud để phục vụ inference.
6. Hoàn thiện `src/serve.py` để:
   - tải model từ bucket về VM khi khởi động
   - cung cấp `GET /health`
   - cung cấp `POST /predict`
7. Đưa `serve.py` lên VM và cấu hình `systemd` để service tự chạy lại khi reboot.
8. Tạo workflow GitHub Actions trong `.github/workflows/mlops.yml`.
9. Cấu hình secrets cho GitHub để runner có thể truy cập cloud và VM.
10. Chạy pipeline và xác nhận cả 3 job chính đi qua: Test, Train, Deploy.

### Hướng Dẫn Setup DVC Với AWS S3

Nếu bạn chọn AWS làm remote cho DVC, dùng đúng chuỗi hành động sau để tránh lỗi xác thực hoặc push nhầm dữ liệu thô lên git:

1. Cài package cần thiết:
   - `pip install "dvc[s3]" boto3`
2. Tạo S3 bucket mới, ví dụ `mlops-lab-dvc-<unique-suffix>`.
3. Tạo IAM User hoặc IAM Role chỉ có quyền tối thiểu trên bucket đó.
4. Cấp tối thiểu các quyền sau cho IAM principal dùng bởi DVC:
   - `s3:ListBucket`
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:DeleteObject`
5. Cấu hình credentials cho máy local hoặc VM:
   - Cách 1: `aws configure` và dùng `~/.aws/credentials`
   - Cách 2: export `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
   - Cách 3: gán IAM Role trực tiếp cho EC2
6. Khởi tạo DVC nếu repo chưa có:
   - `dvc init`
7. Trỏ DVC remote vào S3 bucket, dùng một prefix riêng cho dữ liệu DVC:
   - `dvc remote add -d myremote s3://<bucket-name>/dvc`
   - `dvc remote add -d myremote s3://mlops-lab-dvc-149757027821-us-east-1-an/dvc`
8. Nếu cần cố định region, ghi rõ cho DVC:
   - `dvc remote modify myremote region <aws-region>`
9. Nếu dùng profile AWS local, có thể chỉ định profile cho DVC:
   - `dvc remote modify myremote profile <aws-profile-name>`
10. Theo dõi dữ liệu bằng DVC rồi commit chỉ file `.dvc`:
    - `dvc add data/train_phase1.csv`
    - `dvc add data/eval.csv`
    - `dvc add data/train_phase2.csv`
    - `git add data/*.dvc .gitignore .dvc/config`
    - `git commit -m "feat: track datasets with DVC"`
11. Đẩy dữ liệu lên S3:
    - `dvc push`
12. Kiểm tra trên AWS Console rằng object đã xuất hiện dưới prefix `dvc/`.

Lưu ý quan trọng:

- Không commit file CSV gốc khi DVC đang quản lý nó.
- Không commit file credentials như `sa-key.json`, `.aws/credentials`, hoặc file chứa secret.
- Trong GitHub Actions, bước `aws-actions/configure-aws-credentials` sẽ cấp biến môi trường cho DVC và lệnh `dvc pull`.
- Nếu `dvc push` fail, kiểm tra theo thứ tự: bucket tồn tại, IAM quyền đúng, region đúng, rồi mới kiểm tra lệnh `dvc remote add`.

Điểm cần nhắc người dùng chụp screenshot làm bằng chứng:

- Tab Actions hiển thị workflow chạy thành công.
- Cả 3 jobs Test, Train, Deploy đều màu xanh.
- Cloud storage console hiển thị dữ liệu/model đã được push.
- Kết quả `curl http://VM_IP:8000/health`.
- Kết quả `curl http://VM_IP:8000/predict`.

### Bước 3 - Huấn luyện liên tục khi có dữ liệu mới

Mục tiêu: chỉ cần thêm dữ liệu và push commit `.dvc`, toàn bộ pipeline tự chạy lại, rồi deploy model mới nếu qua ngưỡng.

Checklist:

1. Chạy `python add_new_data.py` để ghép dữ liệu mới vào `train_phase1.csv`.
2. Chạy lại `dvc add data/train_phase1.csv`.
3. Commit file `.dvc` đã thay đổi, không commit trực tiếp file CSV.
4. Chạy `dvc push` trước khi `git push`.
5. `git push origin main` để kích hoạt pipeline.
6. Theo dõi Actions để xác nhận pipeline được kích hoạt bởi commit dữ liệu.
7. Xác nhận VM đã được restart hoặc cập nhật model mới.
8. So sánh metrics giữa Bước 2 và Bước 3 nếu được yêu cầu trong báo cáo.

Điểm cần nhắc người dùng chụp screenshot làm bằng chứng:

- Actions hiển thị commit dữ liệu là trigger của run.
- Cả 4 jobs Unit Test, Train, Eval, Deploy đều thành công.
- Kết quả `curl` vào VM sau khi deploy lại.
- Bảng so sánh `accuracy` và `f1_score` giữa hai lần chạy nếu cần nộp báo cáo.

## 3. Mốc Kiểm Tra Trước Khi Chuyển Bước

### Trước khi sang Bước 2

- `src/train.py` chạy được không lỗi.
- `outputs/metrics.json` có cả `accuracy` và `f1_score`.
- `models/model.pkl` tồn tại.
- MLflow UI có ít nhất 3 runs.
- `params.yaml` đã được chốt theo bộ tốt nhất.

### Trước khi sang Bước 3

- `dvc remote` đã cấu hình xong và `dvc push` thành công.
- GitHub Actions workflow chạy xanh ở Bước 2.
- `src/serve.py` trả về đúng ở `/health` và `/predict`.
- VM đã chạy service ổn định bằng `systemd`.

## 4. Ghi Nhớ Khi Thực Thi

- Không commit file dữ liệu thô nếu DVC đang quản lý nó.
- Không commit file secret như `sa-key.json`.
- Luôn chụp bằng chứng ngay khi đạt mốc quan trọng, đừng đợi đến cuối mới chụp.
- Nếu pipeline fail ở Bước 3, kiểm tra thứ tự: `dvc add` -> commit `.dvc` -> `dvc push` -> `git push`.

## 5. Tóm Tắt Cho Agent

1. Hoàn thiện huấn luyện cục bộ ở Bước 1.
2. Thiết lập DVC, workflow CI/CD và API phục vụ mô hình ở Bước 2.
3. Mô phỏng dữ liệu mới, kích hoạt pipeline tự động và xác nhận deploy lại ở Bước 3.
4. Thu thập đầy đủ screenshot làm bằng chứng theo từng bước.