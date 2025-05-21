let step = 0;
let video = null;
let canvas = null;
let ctx = null;
let imageData = null;

function scanData() {
    const button = document.getElementById('scanButton');
    step = (step + 1) % 3;

    if (step === 0) {
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
    else if (step === 1) {
        button.textContent = '送信';

        if (!video || !canvas || !ctx) {
            alert("カメラやキャンバスが準備できていません。");
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        imageData = canvas.toDataURL("image/png");

        alert("写真を撮影しました！");
    }
    else if (step === 2) {
        button.innerHTML = 'レシート<br>読み取り';

        if (!imageData) {
            alert("写真がありません。先に撮影してください。");
            return;
        }

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
    const rows = document.querySelectorAll("#data-table tr");
    const data = [];

    // 2行目以降を取得
    for (let i = 1; i < rows.length; i++) {
    const cells = rows[i].querySelectorAll("td");
    const rowData = [];
    cells.forEach(cell => rowData.push(cell.innerText.trim()));
    data.push(rowData);
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
        alert("送信成功！");
    } else {
        alert("送信失敗！");
    }
    });
}
