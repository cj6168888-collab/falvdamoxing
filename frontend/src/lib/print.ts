export function handlePrint(elementId?: string) {
  if (elementId) {
    const element = document.getElementById(elementId);
    if (element) {
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head><title>打印</title></head>
            <body>${element.innerHTML}</body>
          </html>
        `);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
        printWindow.close();
      }
    }
  } else {
    window.print();
  }
}
