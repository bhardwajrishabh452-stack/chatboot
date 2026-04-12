const socket = io();
let currentRoom = null;

function startPrivateChat(userId, username) {
    currentRoom = 'private_' + userId;
    socket.emit('join', { room: currentRoom });
    document.getElementById('messages').innerHTML = '';
}

function startTeamChat(teamId, teamName) {
    currentRoom = 'team_' + teamId;
    socket.emit('join', { room: currentRoom });
    document.getElementById('messages').innerHTML = '';
}

function sendMessage() {
    const input = document.getElementById('message-input');
    if(!currentRoom || !input.value) return;
    socket.emit('send_message', {
        room: currentRoom,
        message: input.value
    });
    input.value = '';
}

socket.on('receive_message', data => {
    const li = document.createElement('li');
    li.textContent = `${data.sender}: ${data.message}`;
    document.getElementById('messages').appendChild(li);
});
socket.on('status', data => {
    const li = document.createElement('li');
    li.textContent = `* ${data.msg} *`;
    li.style.fontStyle = 'italic';
    document.getElementById('messages').appendChild(li);
});