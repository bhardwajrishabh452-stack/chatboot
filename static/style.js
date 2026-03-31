var socket;

function initSocket(room, username){
socket = io();
socket.emit("join",{room:room});

socket.on("receive_message",function(data){
let div=document.createElement("div");
div.className="message "+(data.sender===username?"sent":"received");
div.innerHTML="<strong>"+data.sender+"</strong>: "+data.message;
document.getElementById("messages").appendChild(div);
document.getElementById("notify").play();
});

socket.on("online_update",function(users){
let box=document.getElementById("onlineUsers");
if(box){
box.innerHTML="";
users.forEach(u=>{
box.innerHTML+=u+" 🟢<br>";
});
}
});

socket.on("show_typing",function(data){
if(data.user!==username){
document.getElementById("typing").innerHTML=data.user+" typing...";
setTimeout(()=>{document.getElementById("typing").innerHTML="";},2000);
}
});

document.getElementById("fileInput")?.addEventListener("change",function(){
let file=this.files[0];
let formData=new FormData();
formData.append("file",file);

fetch("/upload",{method:"POST",body:formData})
.then(res=>res.json())
.then(data=>{
socket.emit("send_message",{
room:room,
sender:username,
message:"📎 <a href='/static/uploads/"+data.file+"' target='_blank'>"+data.file+"</a>"
});
});
});
}

function sendMessage(room,username){
let msg=document.getElementById("msg").value;
if(msg.trim()=="") return;

socket.emit("send_message",{room:room,sender:username,message:msg});
document.getElementById("msg").value="";
}

function typing(room){
socket.emit("typing",{room:room,user:sessionStorage.getItem("username")});
}

function toggleTheme(){
document.body.classList.toggle("dark");
}