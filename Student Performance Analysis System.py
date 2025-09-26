import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
import tempfile
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ---------- Student Class ----------
class Student:
    def validate_marks(self, mark, subject):
        try:
            mark = float(mark)
            if not (0 <= mark <= 100):
                raise ValueError(f"{subject} mark must be between 0 and 100")
            return mark
        except ValueError as e:
            raise ValueError(f"Invalid {subject} mark: {e}")

    def __init__(self, roll_no, name, math, science, english):
        self.roll_no = roll_no
        self.name = name
        self.math = self.validate_marks(math, "Math")
        self.science = self.validate_marks(science, "Science")
        self.english = self.validate_marks(english, "English")
        self.gpa = self.calculate_gpa()
        self.grade = self.assign_grade()

    def calculate_gpa(self):
        marks = [self.math, self.science, self.english]
        percentage = np.mean(marks)
        return round(percentage / 25, 2)

    def assign_grade(self):
        if self.gpa >= 3.5: return "A"
        elif self.gpa >= 3.0: return "B"
        elif self.gpa >= 2.0: return "C"
        else: return "D"

# ---------- Report Class ----------
class StudentReport:
    def __init__(self, df):
        self.df = df
        self.students = self.create_students()

    def create_students(self):
        return [
            Student(row["roll_no"], row["name"], row["math"], row["science"], row["english"])
            for _, row in self.df.iterrows()
        ]

    def to_dataframe(self):
        return pd.DataFrame([{
            "roll_no": s.roll_no,
            "name": s.name,
            "math": s.math,
            "science": s.science,
            "english": s.english,
            "GPA": s.gpa,
            "Grade": s.grade
        } for s in self.students])

# ---------- PDF Generator ----------
class PDFReportGenerator:
    def __init__(self, df, summary, chart_files):
        self.df = df
        self.summary = summary
        self.chart_files = chart_files

    def generate(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("📊 Student Performance Report", styles['Title']))
        elements.append(Spacer(1, 12))

        # Summary
        elements.append(Paragraph("Summary Statistics", styles['Heading2']))
        summary_table = Table([self.summary.columns.to_list()] + self.summary.values.tolist())
        elements.append(summary_table)
        elements.append(Spacer(1, 12))

        # Charts
        elements.append(Paragraph("Visualizations", styles['Heading2']))
        for chart_file in self.chart_files:
            elements.append(Image(chart_file, width=400, height=250))
            elements.append(Spacer(1, 12))

        # Student-Level
        elements.append(Paragraph("Student-Level Report", styles['Heading2']))
        student_table_data = [["Roll No", "Name", "GPA", "Grade"]]
        for _, row in self.df.iterrows():
            student_table_data.append([row["roll_no"], row["name"], row["GPA"], row["Grade"]])
        student_table = Table(student_table_data, hAlign="LEFT")
        elements.append(student_table)

        # Build
        doc.build(elements)
        buffer.seek(0)
        return buffer

# ---------- Streamlit App ----------
st.set_page_config(page_title="Student Performance Dashboard", layout="wide")
st.title("📊 Student Performance Analysis System")
st.write("Upload a CSV file of student marks and explore insights!")

uploaded_file = st.file_uploader("Upload students.csv", type=["csv"])

if uploaded_file:
    try:
        # Read CSV file
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.stop()

        # Validate columns
        required_columns = ['roll_no', 'name', 'math', 'science', 'english']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.stop()

        # Check for empty or invalid values
        for col in required_columns:
            if df[col].isnull().any():
                st.error(f"Found empty values in column: {col}")
                st.stop()

        # Process students using OOP
        try:
            report = StudentReport(df)
            df = report.to_dataframe()
        except ValueError as e:
            st.error(str(e))
            st.stop()
            
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.stop()

    # Show data
    st.subheader("📌 Student Data")
    st.dataframe(df)

    # CSV Download
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button("📥 Download Analyzed Data (CSV)", csv_buffer.getvalue(),
                       file_name="analyzed_students.csv", mime="text/csv")

    # Statistics
    st.subheader("📊 Summary Statistics")
    summary = df.describe()
    st.write(summary)

    # Charts
    st.subheader("📈 Visualizations")
    chart_files = []

    # Create temporary directory for charts
    with tempfile.TemporaryDirectory() as tmp_dir:
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Average Marks per Subject")
            avg_per_subject = df[["math","science","english"]].mean()
            fig, ax = plt.subplots()
            avg_per_subject.plot(kind="bar", color=["skyblue","lightgreen","salmon"], ax=ax)
            st.pyplot(fig)
            avg_file = os.path.join(tmp_dir, "avg_subjects.png")
            fig.savefig(avg_file)
            chart_files.append(avg_file)

        with col2:
            st.write("### GPA Trend by Roll No")
            fig, ax = plt.subplots()
            ax.plot(df["roll_no"], df["GPA"], marker="o", color="purple")
            st.pyplot(fig)
            gpa_file = os.path.join(tmp_dir, "gpa_trend.png")
            fig.savefig(gpa_file)
            chart_files.append(gpa_file)

        st.write("### Correlation Heatmap")
        fig, ax = plt.subplots()
        corr = df[["math","science","english","GPA"]].corr()
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)
        heatmap_file = os.path.join(tmp_dir, "heatmap.png")
        fig.savefig(heatmap_file)
        chart_files.append(heatmap_file)

        st.write("### Grade Distribution")
        fig, ax = plt.subplots()
        sns.countplot(x="Grade", data=df, palette="Set2", ax=ax)
        st.pyplot(fig)
        grade_file = os.path.join(tmp_dir, "grade_dist.png")
        fig.savefig(grade_file)
        chart_files.append(grade_file)

        # PDF Report
        pdf_gen = PDFReportGenerator(df, summary, chart_files)
        pdf_buffer = pdf_gen.generate()
        st.download_button("📑 Download PDF Report", pdf_buffer,
                           file_name="student_report.pdf", mime="application/pdf")
        # Temporary files will be automatically cleaned up when exiting this block

else:
    st.info("👆 Upload a CSV file to get started.")
