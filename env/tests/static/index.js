let step = 0;
let video = null;
let canvas = null;
let ctx = null;
let imageData = null;

//jsonデータを表示
fetch('/upload')
    .then(response => response.json())
    .then(data => {
        const table = document.getElementById('editableTable');
        let rows = data.map(row =>
            '<tr>' + row.map(cell => '<td>${cell}</td>').join('') + '</tr>'
        ).join('');
        table.innerHTML = rows;
    });

document.addEventListener("DOMContentLoaded", function() { 
    const table = document.getElementById('editableTable');

    //セル編集時
    function onCellEdit(e) {
        console.log("edit");
        const lastRow = table.rows[table.rows.length -1];
        if(e.target.parentElement === lastRow){addRow();}
    }

    //新規セル追加
    function addRow() {
        const row = table.insertRow();
        for(let i=0; i<4; i++){
            const cell = row.insertCell();
            cell.innerHTML = "&nbsp;";
            cell.contentEditable = "true";
            cell.addEventListener("input", onCellEdit);  //新規セルにonCellEditを追加
        }
        console.log("addRow");
    }
    addRow();
});

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

document.getElementById('uploadInput').addEventListener('change', sendImage);

// 画像ファイルを送信
function sendImage(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = function () {
        const imageData = reader.result; // Base64 データ (data:image/jpeg;base64,...)
        fetch("/receipts/upload", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: imageData })
        })
        .then(res => res.text())
        .then(data => {
            alert("送信完了");
            console.log(data);
        })
        .catch(err => {
            alert("送信エラー: " + err);
        });
    };
    reader.readAsDataURL(file);
}


// 撮影して送信
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
    }
    else if (step === 0) {
        button.innerHTML = 'レシート<br>読み取り';

        if (!video || !canvas || !ctx) {
            alert("カメラやキャンバスが準備できていません。");
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        imageData = canvas.toDataURL("image/png");

        alert("写真を撮影しました！");

        //Flaskに送信
        fetch("/receipts/upload", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: imageData })
        })
        .then(res => res.text())
        .then(data => {
            alert("画像をサーバーに送信しました！");
            console.log(data);
        })
        .catch(err => {
            alert("送信エラー: " + err);
        });
    }
}

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

    // Pythonに送信する（例: /submit にPOST）
    fetch("/receipts/submit", {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ records: data })
    })
    .then(response => {
    if (response.ok) {
        alert("送信成功");
    } else {
        alert("送信失敗");
    }
    });
}
