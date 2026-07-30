# generate_poem.py
import argparse
import importlib.util
import os
import sys


def load_poem_list(source_path):
    """
    تحميل المتغير poem_list ديناميكيًا من ملف بايثون مُعطى مساره
    """
    source_path = os.path.abspath(source_path)

    if not os.path.isfile(source_path):
        raise FileNotFoundError(f"الملف غير موجود: {source_path}")

    module_name = os.path.splitext(os.path.basename(source_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, source_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"تعذر تحميل الملف كوحدة بايثون: {source_path}")

    module = importlib.util.module_from_spec(spec)
    # يسمح هذا للملف المحمَّل باستيراد وحدات أخرى بجواره (نفس المجلد) إن وجدت
    sys.path.insert(0, os.path.dirname(source_path))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    if not hasattr(module, "poem_list"):
        raise AttributeError(
            f"الملف '{source_path}' لا يحتوي على متغير باسم 'poem_list'"
        )

    return module.poem_list


def generate_html(poems, output_file="amro_bin_kalthoum.html"):
    """
    توليد ملف HTML لعرض الأبيات الشعرية
    """

    # بناء محتوى الأبيات بتنسيق HTML
    verses_html = ""
    for i, (first_hemistich, second_hemistich) in enumerate(poems, 1):
        verses_html += f"""
        <div class="verse">
            <div class="verse-number">{i}</div>
            <div class="hemistich first">{first_hemistich}</div>
            <div class="hemistich second">{second_hemistich}</div>
        </div>
        """

    # قالب HTML كامل
    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>قصيدة عمرو بن كلثوم</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Amiri', 'Traditional Arabic', 'Times New Roman', serif;
            background: linear-gradient(145deg, #1a0a05 0%, #2d1810 50%, #1a0a05 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 30px;
        }}
        
        .container {{
            background: linear-gradient(180deg, #fdf6e3 0%, #f5e6c8 100%);
            max-width: 900px;
            width: 100%;
            padding: 50px 60px;
            border-radius: 30px;
            box-shadow: 
                0 20px 60px rgba(0,0,0,0.8),
                0 0 0 3px #c49a6c,
                0 0 0 8px #8b6b4d,
                0 0 0 12px #5a3d2b;
            position: relative;
        }}
        
        .container::before {{
            content: "◈";
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 40px;
            color: #c49a6c;
            text-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }}
        
        .title {{
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            color: #4a2a1a;
            padding-bottom: 20px;
            margin-bottom: 30px;
            border-bottom: 3px double #8b6b4d;
            position: relative;
        }}
        
        .title::after {{
            content: "✧";
            position: absolute;
            bottom: -18px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 24px;
            color: #8b6b4d;
            background: #f5e6c8;
            padding: 0 15px;
        }}
        
        .subtitle {{
            text-align: center;
            font-size: 18px;
            color: #6b4f3a;
            margin-bottom: 40px;
            font-style: italic;
            letter-spacing: 2px;
        }}
        
        .verse {{
            display: grid;
            grid-template-columns: 40px 1fr 1fr;
            gap: 15px;
            align-items: center;
            padding: 18px 20px;
            margin-bottom: 12px;
            background: rgba(255, 248, 235, 0.7);
            border-radius: 15px;
            border-right: 4px solid #c49a6c;
            transition: all 0.3s ease;
        }}
        
        .verse:hover {{
            background: rgba(255, 248, 235, 0.95);
            transform: translateX(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        
        .verse-number {{
            font-size: 20px;
            font-weight: bold;
            color: #8b6b4d;
            text-align: center;
            font-family: 'Times New Roman', serif;
            opacity: 0.6;
        }}
        
        .hemistich {{
            font-size: 24px;
            line-height: 1.8;
            color: #2d1810;
            padding: 5px 10px;
            text-align: center;
            font-weight: 500;
        }}
        
        .hemistich.first {{
            border-left: 2px dashed #c49a6c;
            padding-left: 20px;
        }}
        
        .hemistich.second {{
            padding-right: 20px;
        }}
        
        .hemistich::before {{
            content: "❝";
            font-size: 14px;
            color: #8b6b4d;
            opacity: 0.4;
            margin-left: 5px;
        }}
        
        .hemistich::after {{
            content: "❞";
            font-size: 14px;
            color: #8b6b4d;
            opacity: 0.4;
            margin-right: 5px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 35px;
            padding-top: 20px;
            border-top: 2px solid #d4b896;
            color: #6b4f3a;
            font-size: 16px;
            letter-spacing: 1px;
        }}
        
        .footer span {{
            display: inline-block;
            margin: 0 10px;
            color: #8b6b4d;
        }}
        
        @media (max-width: 700px) {{
            .container {{
                padding: 30px 20px;
            }}
            
            .verse {{
                grid-template-columns: 1fr;
                gap: 5px;
                text-align: center;
                padding: 15px;
            }}
            
            .verse-number {{
                font-size: 16px;
                margin-bottom: 5px;
            }}
            
            .hemistich {{
                font-size: 20px;
                line-height: 1.6;
            }}
            
            .hemistich.first {{
                border-left: none;
                border-bottom: 1px dashed #c49a6c;
                padding-left: 0;
                padding-bottom: 8px;
            }}
            
            .hemistich.second {{
                padding-right: 0;
                padding-top: 8px;
            }}
            
            .title {{
                font-size: 24px;
            }}
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
                border: 1px solid #ccc;
            }}
            .verse:hover {{
                transform: none;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">قصيدة عمرو بن كلثوم</div>
        <div class="subtitle">✦ من معلقات العرب ✦</div>
        
        {verses_html}
        
        <div class="footer">
            <span>◈</span> 
            قال عمرو بن كلثوم التغلبي 
            <span>◈</span>
        </div>
    </div>
</body>
</html>"""

    # كتابة الملف
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ تم إنشاء الملف: {output_file}")
    print(f"📍 المسار الكامل: {os.path.abspath(output_file)}")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="توليد صفحة HTML لعرض أبيات شعرية من ملف بايثون يحتوي على poem_list"
    )
    parser.add_argument(
        "poem_file",
        help="مسار ملف بايثون (.py) يحتوي على المتغير poem_list",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="amro_bin_kalthoum.html",
        help="اسم/مسار ملف الإخراج (افتراضيًا: amro_bin_kalthoum.html)",
    )
    args = parser.parse_args()

    poems = load_poem_list(args.poem_file)
    generate_html(poems, args.output)


if __name__ == "__main__":
    main()
