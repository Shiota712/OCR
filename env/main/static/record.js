
document.addEventListener("DOMContentLoaded", () => {
    displayLog();
});

// jsonデータをテーブルに反映する
function displayLog() {
    const tableBody = document.getElementById('editableTable').querySelector('tbody');
    const totalPriceElem = document.getElementById('totalPrice');
    const balanceElem = document.getElementById('balance');

    fetch('/record/getJson')
        .then(response => response.json())
        .then(data => {
            let total = 0;
            data.reverse().forEach(item => {
                total += Number(item.price) || 0;  // priceを数値化して合計

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.date}</td>
                    <td>${item.item_name}</td>
                    <td>${item.category}</td>
                    <td>${item.note}</td>
                    <td>${item.price}</td>
                `;
                tableBody.appendChild(row);
            });

            totalPriceElem.textContent = total.toLocaleString();  // 3桁区切り表示
            fetch('/record/balance')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'ok') {
                        const balanceElem = document.getElementById('balance');
                        balanceElem.textContent = Number(data.balance).toLocaleString();
                    } else {
                        console.error('残高取得エラー:', data.message);
                    }
                })
                .catch(err => console.error('通信エラー:', err));
        })
        .catch(error => {
            console.error('ログの取得に失敗しました:', error);
        });
}