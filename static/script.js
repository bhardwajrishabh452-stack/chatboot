const socket = io();
let selectedUser = null;
let selectedTeam = null;

const userList = document.getElementById("user-list");
const teamList = document.getElementById("team-list");
const messages = document.getElementById("messages");
const header = document.getElementById("chat-header");
const input = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");

// ---------------- SELECT USER ----------------
userList.querySelectorAll("li").forEach(li=>{
    li.addEventListener("click", ()=>{
        selectedUser = li.dataset.username;
        selectedTeam = null;
        header.innerText = "Private: " + selectedUser;
        messages.innerHTML = "";
    });
});

// ---------------- SELECT TEAM ----------------
teamList.querySelectorAll("li").forEach(li=>{
    li.addEventListener("click", ()=>{
        selectedTeam = li.dataset.team;
        selectedUser = null;
        header.innerText = "Team: " + li.innerText;
        messages.innerHTML = "";
    });
});

// ---------------- SEND MESSAGE ----------------
sendBtn.addEventListener("click", ()=>{
    const msg = input.value;
    if(!msg) return;
    socket.emit("send",{msg:msg,recv:selectedUser,team:selectedTeam});
    input.value="";
});

// ---------------- RECEIVE MESSAGE ----------------
socket.on("receive", data=>{
    if((data.recv && data.recv===selectedUser) || (data.team && data.team===selectedTeam)){
        const div = document.createElement("div");
        div.innerHTML = "<b>"+data.u+":</b> "+data.m;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }
});

// ---------------- ONLINE USERS ----------------
socket.on("online", users=>{
    userList.querySelectorAll("li").forEach(li=>{
        if(users.includes(li.dataset.username)){
            li.classList.add("online"); li.classList.remove("offline");
        } else {
            li.classList.add("offline"); li.classList.remove("online");
        }
    });
});