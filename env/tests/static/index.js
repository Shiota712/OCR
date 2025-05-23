let step = 0;
let video = null;
let canvas = null;
let ctx = null;

document.addEventListener("DOMContentLoaded", () => {
    fetch('/receipts/session-user')
        .then(res => {
            if (!res.ok) throw new Error("ログインしていません");
            return res.json();
        })
        .then(data => {
            document.getElementById('username').textContent = data.username;
        })
        .catch(err => {
            console.log(err.message);
            document.getElementById('username').textContent = 'ゲスト';
        });
    
    const table = document.getElementById('editableTable');
    addRow();  // 最初の行追加
});

// 新しい行を追加
function addRow() {
    const table = document.getElementById('editableTable');
    const row = table.insertRow();
    for (let i = 0; i < 5; i++) {
        const cell = row.insertCell();
        cell.innerHTML = "&nbsp;";
        cell.contentEditable = "true";
        cell.addEventListener("input", onCellEdit);
    }
}

// 編集されたときに最終行なら新しい行を追加
function onCellEdit(e) {
    const table = document.getElementById('editableTable');
    const lastRow = table.rows[table.rows.length - 1];
    if (e.target.parentElement === lastRow) {
        addRow();
    }
}


// レシート読み込み
function showOptions() {
  const choice = confirm("カメラを起動しますか？\n[OK]: カメラ起動\n[キャンセル]: 画像をアップロード");
  if (choice) {
    // カメラ起動
    scanData();
  } else {
    // ファイルアップロード
    document.getElementById('uploadInput').click();
  }
}

document.getElementById('uploadInput').addEventListener('change', uploadImage);

// 画像をアップロード
function uploadImage(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
        const imageData = reader.result;
        uploadImageToServer(imageData);
    };
    reader.readAsDataURL(file);
}

// 撮影してアップロード
function scanData() {
    const button = document.getElementById('loadButton');
    step = (step + 1) % 2;

    if (step === 1) {
        button.innerHTML = '撮影';

        if (!video) video = document.getElementById('video');
        if (!canvas) canvas = document.getElementById('canvas');
        if (!ctx && canvas) ctx = canvas.getContext('2d');

        // カメラ起動
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                video.style.display = 'block';
                video.onloadedmetadata = () => {
                    video.play();
                };
            })
            .catch(err => {
                alert("カメラ起動エラー: " + err);
            });
    } else {
        button.innerHTML = 'レシート<br>読み取り';

        if (!video || !canvas || !ctx) {
            alert("カメラやキャンバスが準備できていません。");
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageData = canvas.toDataURL("image/png");
        alert("写真を撮影しました！");
        uploadImageToServer(imageData);
    }
}

// 画像ファイルを送信
async function uploadImageToServer(imageData) {
    try {
        const response = await fetch("/receipts/upload", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: imageData })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "アップロードに失敗しました");

        populateTable(data);

    } catch (err) {
        alert("送信エラー: " + err.message);
    }
}

// jsonデータをテーブルに反映する
function populateTable(data) {
    const tableBody = document.getElementById('editableTable').querySelector('tbody');
    const rows = tableBody.querySelectorAll('tr');

    // 不必要な行を削除
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const isEmpty = [...cells].every(cell => cell.innerText.trim() === "" || cell.innerText.trim() === "\u00A0"); // 空文字または&nbsp;

        if (isEmpty) {
            row.remove();
        }
    });

    const today = new Date().toISOString().split('T')[0];

    data.forEach(item => {
        const row = document.createElement('tr');
        row.setAttribute("contenteditable", "true");
        row.innerHTML = `
            <td>${today}</td>
            <td>${item.item_name}</td>
            <td>${item.category}</td>
            <td>${item.note}</td>
            <td>${item.price}</td>
        `;
        tableBody.appendChild(row);
    });
    addRow();
}


// 内容を確定し、保存、ログに表示
function submitData() {
    const rows = document.querySelectorAll("#editableTable tr");
    const data = [];

    // 2行目以降を取得
    for (let i = 1; i < rows.length; i++) { // ヘッダー行は除く
        const cells = rows[i].querySelectorAll("td");
        const rowData = [];
        cells.forEach(cell => rowData.push(cell.innerText.trim()));
        // 空行を除外（全セル空白）
        if (rowData.some(value => value !== "")) {
            data.push(rowData);
        }
    }

    fetch("/receipts/submit", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ records: data })
    })
    .then(res => {
        alert(res.ok ? "送信成功" : "送信失敗");
    });

    // Tableをリセット
    document.querySelector('#editableTable tbody').innerHTML = '';
    addRow();
}
