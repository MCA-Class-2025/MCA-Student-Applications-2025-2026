export const exportToPDF = (title: string, contentHtml: string, filename: string) => {
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to export downloadable PDF files.');
    return;
  }

  const htmlTemplate = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>${title} - PrepGenius AI Export</title>
        <style>
          body {
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #1e293b;
            padding: 40px;
            line-height: 1.6;
          }
          .header {
            border-bottom: 3px solid #6366f1;
            padding-bottom: 15px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .logo {
            font-size: 24px;
            font-weight: 800;
            color: #6366f1;
          }
          .tag {
            font-size: 12px;
            background: #e0e7ff;
            color: #4338ca;
            padding: 4px 10px;
            border-radius: 999px;
            font-weight: 600;
          }
          .content {
            font-size: 14px;
          }
          h1, h2, h3 { color: #0f172a; margin-top: 20px; }
          .card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
          }
          .footer {
            margin-top: 40px;
            border-top: 1px solid #e2e8f0;
            padding-top: 15px;
            font-size: 11px;
            color: #64748b;
            text-align: center;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo">PrepGenius AI</div>
          <div class="tag">${title}</div>
        </div>

        <div class="content">
          ${contentHtml}
        </div>

        <div class="footer">
          Generated automatically by PrepGenius AI Study Ecosystem • ${new Date().toLocaleDateString()}
        </div>

        <script>
          window.onload = function() {
            window.print();
          };
        </script>
      </body>
    </html>
  `;

  printWindow.document.write(htmlTemplate);
  printWindow.document.close();
};
