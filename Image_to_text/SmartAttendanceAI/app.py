# SmartAttendance AI (LLM Vision-based)
# ------------------------------------
# pip install openai pandas openpyxl streamlit pillow

import streamlit as st
from openai import OpenAI
from datetime import date
import pandas as pd
from io import BytesIO
import base64

client = OpenAI(api_key="YOUR_GPT5_API_KEY")  # Replace with your key

st.set_page_config(page_title="SmartAttendance AI", page_icon="🎓")
st.title("🎓 SmartAttendance AI – GPT-5 Vision Edition")
st.write("Upload a classroom image and student reference photos; GPT-5 Vision will identify who’s present.")

# Uploads
classroom_img = st.file_uploader("Upload classroom image", type=["jpg","jpeg","png"])
ref_images = st.file_uploader("Upload student reference images (multiple allowed)", type=["jpg","jpeg","png"], accept_multiple_files=True)

if classroom_img and ref_images:
    st.image(classroom_img, caption="Classroom Image", use_column_width=True)
    st.info(f"{len(ref_images)} reference images uploaded.")

    if st.button("Mark Attendance with GPT-5 Vision"):
        # Convert uploaded files to base64 URLs for GPT-5 input
        def to_data_uri(file):
            b64 = base64.b64encode(file.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{b64}"

        classroom_uri = to_data_uri(classroom_img)
        ref_data = []
        for file in ref_images:
            name = file.name.split(".")[0]
            uri = to_data_uri(file)
            ref_data.append({"name": name, "uri": uri})

        # Construct the LLM prompt
        prompt = f"""
        You are SmartAttendance GPT, an AI vision system that marks classroom attendance.

        Compare the classroom image with the provided reference student images.
        Identify which students are visible (present) and which are missing (absent).

        Return the result as a JSON object like:
        {{
          "date": "{str(date.today())}",
          "present": ["Rahul","Sneha"],
          "absent": ["Priya"]
        }}

        Only include names that match the reference photos. 
        Base your analysis on clear visual similarity of faces.
        """

        # Prepare message structure for GPT-5 Vision
        vision_inputs = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": classroom_uri},
        ]
        for r in ref_data:
            vision_inputs.append({"type": "image_url", "image_url": r["uri"]})

        # Send to GPT-5
        with st.spinner("Analyzing image with GPT-5 Vision..."):
            response = client.chat.completions.create(
                model="gpt-5-vision",
                messages=[{"role": "user", "content": vision_inputs}],
                temperature=0.1
            )

        output = response.choices[0].message.content
        st.subheader("📋 GPT-5 Output")
        st.code(output)

        # Parse GPT output safely
        try:
            import json
            result = json.loads(output)
            present = result.get("present", [])
            absent = result.get("absent", [])
        except:
            st.error("⚠️ Could not parse model output as JSON. Check result above.")
            present, absent = [], []

        # Write to Excel
        if present or absent:
            all_students = [r["name"] for r in ref_data]
            df = pd.DataFrame({
                "Date": [str(date.today())]*len(all_students),
                "Student": all_students,
                "Attendance": ["Present" if s in present else "Absent" for s in all_students]
            })

            file_name = "attendance.xlsx"
            df.to_excel(file_name, index=False)
            st.success("✅ Attendance saved to attendance.xlsx")

            # Download link
            with open(file_name, "rb") as f:
                b = f.read()
                st.download_button("📥 Download Excel Report", data=b, file_name=file_name, mime="application/vnd.ms-excel")

            # Summary
            st.write(f"**Present ({len(present)}):** {', '.join(present)}")
            st.write(f"**Absent ({len(absent)}):** {', '.join(absent)}")

