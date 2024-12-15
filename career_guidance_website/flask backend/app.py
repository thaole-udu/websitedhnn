from flask import Flask, render_template, request, redirect, url_for,flash
import json
from  flask import session
from datetime import datetime
import os
app = Flask(__name__)
app.secret_key = 'b1e9a8f45c3d12f7d8e6faef3b52a742'
app.secret_key = 'your_secret_key'  # Để sử dụng flash cho thông báo tạm thời
@app.route('/')
def home():
    return render_template('index.html')
# Tải dữ liệu ngành nghề và trường học từ file JSON
def load_data():
    with open('flask backend\\data1.json', 'r', encoding='utf-8') as f:
        career_data = json.load(f)
    with open('flask backend\\data2.json', 'r', encoding='utf-8') as f:
        school_data = json.load(f)
    return career_data, school_data

# Hàm xử lý học phí
def parse_tuition(tuition_str):
    if tuition_str == 0 or tuition_str == "0" or tuition_str.strip() == "":
        return (0, 0)
    tuition_str = tuition_str.replace(",", "").strip()
    try:
        if ">" in tuition_str:
            return int(tuition_str.replace(">", "").strip()), float('inf')
        elif "<" in tuition_str:
            return 0, int(tuition_str.replace("<", "").strip())
        elif "-" in tuition_str:
            low, high = map(int, tuition_str.split('-'))
            return low, high
        else:
            value = int(tuition_str)
            return value, value
    except ValueError:
        print(f"Warning: Unable to parse tuition value from '{tuition_str}'. Defaulting to (0, 0).")
        return (0, 0)

# Lọc trường học theo học phí
def filter_school_by_tuition(school_data, max_tuition):
    filtered_schools = []
    for school in school_data:
        min_tuition, max_tuition_in_data = parse_tuition(school["tuition"])
        if min_tuition == 0 and max_tuition_in_data == 0:
            continue
        if min_tuition <= max_tuition and max_tuition_in_data <= max_tuition:
            filtered_schools.append(school)
    return filtered_schools
# Lọc trường học theo ngành học
def filter_school_by_major(school_data, majors):
    filtered_schools = []
    for school in school_data:
        school_majors = school.get("majors", [])
        if any(major in school_majors for major in majors):
            filtered_schools.append(school)
    return filtered_schools
# Lọc trường học theo khu vực
def filter_school_by_region(school_data, region):
    region = f"Miền {region.capitalize()}"
    # Chuyển đổi chuỗi thành danh sách các vùng miền, loại bỏ khoảng trắng
    return [school for school in school_data if school["region"] == region]

# Hàm tìm ngành nghề theo MBTI
def find_careers(mbti_type, career_data):
    unique_industries = set()
    careers = []
    for career in career_data:
        if mbti_type in career["mbti_type"].split(", "):
            industry = career["industries"]
            if industry not in unique_industries:
                unique_industries.add(industry)
                careers.append(industry)
    return careers

# Hàm tìm ngành học theo MBTI
def find_majors(mbti_type, major_data):
    unique_majors = set()
    majors = []
    for major in major_data:
        if mbti_type in major["mbti_type"].split(", "):
            major_name = major["majors"]
            if major_name not in unique_majors:
                unique_majors.add(major_name)
                majors.append(major_name)
    return majors

# Hàm tính toán MBTI từ câu trả lời
def calculate_mbti(answers):
    
    # Các nhóm điểm MBTI
    scores = {
        'E': 0, 'I': 0,  # Hướng ngoại (E) và hướng nội (I)
        'S': 0, 'N': 0,  # Cảm giác (S) và trực giác (N)
        'T': 0, 'F': 0,  # Lý trí (T) và tình cảm (F)
        'J': 0, 'P': 0   # Nguyên tắc (J) và linh hoạt (P)
    }

    # Mapping các câu hỏi vào nhóm điểm
    question_mapping = [
        ('E', 'I'), ('S', 'N'), ('S', 'N'), ('T', 'F'), ('T', 'F'), ('J', 'P'),
        ('J', 'P'), ('E', 'I'), ('S', 'N'), ('S', 'N'), ('T', 'F'), ('T', 'F'),
        ('J', 'P'), ('J', 'P'), ('E', 'I'), ('S', 'N'), ('S', 'N'), ('T', 'F'),
        ('T', 'F'), ('J', 'P'), ('J', 'P'), ('E', 'I'), ('S', 'N'), ('S', 'N'),
        ('T', 'F'), ('T', 'F'), ('J', 'P'), ('J', 'P'), ('E', 'I'), ('S', 'N'),
        ('S', 'N'), ('T', 'F'), ('T', 'F'), ('J', 'P'), ('J', 'P'), ('E', 'I'),
        ('S', 'N'), ('S', 'N'), ('T', 'F'), ('T', 'F'), ('J', 'P'), ('J', 'P'),
        ('E', 'I'), ('S', 'N'), ('S', 'N'), ('T', 'F'), ('T', 'F'), ('J', 'P'),
        ('J', 'P'), ('E', 'I'), ('S', 'N'), ('S', 'N'), ('T', 'F'), ('T', 'F'),
        ('J', 'P'), ('J', 'P'), ('E', 'I'), ('S', 'N'), ('S', 'N'), ('T', 'F'),
        ('T', 'F'), ('J', 'P'), ('J', 'P'), ('E', 'I'), ('S', 'N'), ('S', 'N'),
        ('T', 'F'), ('T', 'F'), ('J', 'P'), ('J', 'P')
    ]

    # Tính điểm dựa trên câu trả lời
    for i, answer in enumerate(answers):
        if i >= len(question_mapping):
            break  # Dừng nếu vượt quá số câu hỏi trong mapping
        trait_a, trait_b = question_mapping[i]
        if answer == 'a':
            scores[trait_a] += 1
        elif answer == 'b':
            scores[trait_b] += 1

    # Xác định loại MBTI từ điểm
    mbti_type = ''.join([
        'E' if scores['E'] > scores['I'] else 'I',
        'S' if scores['S'] > scores['N'] else 'N',
        'T' if scores['T'] > scores['F'] else 'F',
        'J' if scores['J'] > scores['P'] else 'P'
    ])

    return mbti_type

@app.route('/career_guidance')
def career_guidance():
    return render_template('career_guidance.html')

# Route hiển thị trang bài test MBTI
@app.route('/mini_test', methods=['GET', 'POST'])
def mini_test():
    with open('flask backend\\questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    if request.method == 'POST':
        answers = [request.form.get(f'answer_{i}') for i in range(len(questions))]
        mbti_type = calculate_mbti(answers)
        session['mbti_type'] = mbti_type  # Lưu MBTI type vào session
        print(f"MBTI type trong /mini_test: {mbti_type}")
        return redirect(url_for('submit')) 
    
    return render_template('mini_test.html', questions=questions)
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    mbti_type = session.get('mbti_type')  # Lấy MBTI type từ session
    if not mbti_type:
        return "Không tìm thấy MBTI type. Vui lòng làm lại bài test."
    
    if request.method == 'POST':
        # Lấy các giá trị từ form
        name = request.form['name']
        age = request.form['age']
        max_tuition = int(request.form['tuition'])
        region = request.form['region']
        
        # Tải dữ liệu và tìm ngành nghề, ngành học
        career_data, school_data = load_data()
        careers = find_careers(mbti_type, career_data) or ["Không tìm thấy ngành nghề phù hợp."]
        majors = find_majors(mbti_type, career_data) or ["Không tìm thấy ngành học phù hợp."]
        
        # Lọc trường học
        schools_by_tuition = filter_school_by_tuition(school_data, max_tuition)
        schools_by_region = filter_school_by_region(schools_by_tuition, region)
        suitable_schools = filter_school_by_major(schools_by_region, majors) or [{"name": "Không tìm thấy trường đại học phù hợp.", "tuition": "", "region": ""}]
        
        # Lưu kết quả và trả về kết quả
        result = {
            "name": name,
            "age": age,
            "mbti_type": mbti_type,
            "careers": careers,
            "majors": majors,
            "suitable_schools": suitable_schools,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_test_results(result)
        return render_template('result.html', result=result)
    
    return render_template('submit.html', mbti_type=mbti_type)

# Lưu kết quả vào file JSON
def save_test_results(result):
    file_path = 'flask backend\\test_results.json'

    # Kiểm tra nếu file đã tồn tại
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)  # Đọc dữ liệu hiện tại
                if not isinstance(data, list):
                    data = []  # Đảm bảo dữ liệu là một danh sách
            except json.JSONDecodeError:
                data = []  # Nếu file rỗng hoặc không hợp lệ
    else:
        data = []  # Tạo danh sách mới nếu file không tồn tại

    # Thêm kết quả mới vào danh sách
    data.append(result)

    # Ghi lại toàn bộ dữ liệu vào file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
# Hàm lưu phản hồi
def save_feedback(name, feedback, rating):
    feedback_entry = {
        "name": name,
        "feedback": feedback,
        "rating": rating,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open('flask backend\\feedback.json', 'a', encoding='utf-8') as f:
        json.dump(feedback_entry, f, ensure_ascii=False)
        f.write("\n")

# Hàm đọc phản hồi từ file
def load_feedbacks():
    feedbacks = []
    try:
        with open('flask backend\\feedback.json', 'r', encoding='utf-8') as f:
            for line in f:
                feedbacks.append(json.loads(line.strip()))
    except FileNotFoundError:
        pass  # Nếu file chưa tồn tại, trả về danh sách rỗng
    return feedbacks

# Trang phản hồi và đánh giá
@app.route('/feedback')
def feedback():
    feedbacks = load_feedbacks()  # Đọc phản hồi từ file
    return render_template('feedback.html', feedbacks=feedbacks)

# Xử lý form phản hồi
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    feedback = request.form['feedback']
    rating = request.form['rating']
    save_feedback(name, feedback, rating)
    # Hiển thị thông báo cảm ơn
    flash('Cảm ơn bạn đã gửi phản hồi!')
    return redirect(url_for('feedback'))  # Quay lại trang phản hồi
@app.route('/dashboard')
def dashboard():
    try:
        # Đọc dữ liệu từ file JSON
        with open('flask backend\\test_results.json', 'r', encoding='utf-8') as file:
            results = json.load(file)

        # Tính tổng số người dùng
        total_users = len(results)

        # Thống kê loại MBTI phổ biến
        mbti_stats = {}
        career_stats = {}

        for user in results:
            # Thống kê MBTI
            mbti = user.get('mbti_type', 'Không xác định')
            mbti_stats[mbti] = mbti_stats.get(mbti, 0) + 1

            # Thống kê ngành nghề
            for career in user.get('careers', []):
                career_stats[career] = career_stats.get(career, 0) + 1

        # Truyền dữ liệu vào template
        return render_template(
            'dashboard.html',
            total_users=total_users,
            mbti_stats=mbti_stats,
            career_stats=career_stats,
            results=results
        )
    except Exception as e:
        return f"Lỗi khi xử lý dữ liệu: {e}"
@app.route('/qa')
def qa():
    return render_template('qa.html')
 
if __name__ == '__main__':
    app.run(debug=True)