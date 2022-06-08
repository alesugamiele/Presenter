self.onmessage = function(e) {
    if (e.data !== undefined) {
        var data = e.data.split("||");
        var url = data[0];
        var params = data[1];
        send_status(url, params);
    }
}

function send_status(url, params) {
  const Http = new XMLHttpRequest();
  Http.open("POST", url, true);
  Http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

  Http.onreadystatechange = (e) => {
    var status = Http.status;
    if(Http.readyState === XMLHttpRequest.DONE) {
      self.postMessage(Http.responseText);
    }
  }
  Http.send(params);
}