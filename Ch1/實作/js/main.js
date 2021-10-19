$(document).ready(function(){
    const backend_path = "http://127.0.0.1:8080/"; // 輸入後端連接的網址，若使用web.py框架預設為http://127.0.0.1:8080/
    setInterval(postMessage, 1000); //　每 1 秒執行一次 postMessage 向後端要門鈴目前的狀況     
    
    function postMessage(){// 處理和後端連接
        let msg = "door_status" // 要傳給後端的訊息
        sending_data = { "msg" : msg};
        json = JSON.stringify(sending_data); // 轉換成 json 格式
        $.post( backend_path, json, function( data_from_backend ) { 
        data = JSON.parse(data_from_backend); // 將 json 轉換成 js 的物件
        console.log(data) // 將變量輸出到瀏覽器的控制台中，在瀏覽器中Crtl+Shift+i開啟控制台後可以看到接收到的資料轉換過後的樣子
        var element = document.getElementById("door_status"); // 用html中設定的ID找到匹配的元素
       elemet.innerHTML += "Connected to backend " + data.results; // 更改該元素當中的html，data.results為後端來的資料
        })
    }
})
