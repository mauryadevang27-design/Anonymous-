import sys

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('''        body { 
            font-family: var(--font-sans);
            background-color: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(16, 185, 129, 0.04), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(16, 185, 129, 0.04), transparent 25%);
        }''', '''        body { 
            font-family: var(--font-sans);
            background-color: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(16, 185, 129, 0.05), transparent 30%),
                radial-gradient(circle at 85% 30%, rgba(16, 185, 129, 0.05), transparent 30%);
            background-size: 200% 200%;
            animation: bgShift 15s ease-in-out infinite;
        }''')

content = content.replace('''        .container {
            background: var(--container-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 20px rgba(16, 185, 129, 0.05);
            width: 95%;
            max-width: 480px;
            overflow: hidden;
            position: relative;
        }''', '''        .container {
            background: var(--container-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 20px rgba(16, 185, 129, 0.05);
            width: 95%;
            max-width: 480px;
            overflow: hidden;
            position: relative;
            animation: popIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }''')

content = content.replace('''        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }''', '''        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        
        @keyframes fadeInSlideUp {
            0% { opacity: 0; transform: translateY(15px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes popIn {
            0% { opacity: 0; transform: scale(0.96); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        @keyframes bgShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }''')

content = content.replace('''        .input-group {
            margin-bottom: 20px;
        }''', '''        .input-group {
            margin-bottom: 20px;
            opacity: 0;
            animation: fadeInSlideUp 0.5s ease-out forwards;
        }
        .input-group:nth-child(1) { animation-delay: 0.1s; }
        .input-group:nth-child(2) { animation-delay: 0.2s; }
        .input-group:nth-child(3) { animation-delay: 0.3s; }''')

content = content.replace('''        .btn-join {
            width: 100%;
            padding: 14px;
            background: var(--accent-green);
            color: #fff;
            border: none;
            border-radius: 10px;
            font-family: var(--font-sans);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 10px;
        }''', '''        .btn-join {
            width: 100%;
            padding: 14px;
            background: var(--accent-green);
            color: #fff;
            border: none;
            border-radius: 10px;
            font-family: var(--font-sans);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 10px;
            opacity: 0;
            animation: fadeInSlideUp 0.5s ease-out forwards;
            animation-delay: 0.4s;
        }''')

content = content.replace('''        .message {
            margin-bottom: 15px;
            max-width: 85%;
            word-wrap: break-word;
            clear: both;
        }''', '''        .message {
            margin-bottom: 15px;
            max-width: 85%;
            word-wrap: break-word;
            clear: both;
            opacity: 0;
            animation: fadeInSlideUp 0.3s ease-out forwards;
        }''')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)


