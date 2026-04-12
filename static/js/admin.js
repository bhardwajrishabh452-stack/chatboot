// Admin CRUD operations
function createUser(){
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-password').value;
    if(!username || !password) return alert('Enter values');
    fetch('/admin/create_user', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({username, password})
    }).then(res => res.json()).then(data=>{
        if(data.success) location.reload();
        else alert(data.error);
    });
}

function deleteUser(userId){
    fetch(`/admin/delete_user/${userId}`, {method:'DELETE'})
    .then(res=>res.json()).then(data=>{
        if(data.success) location.reload();
    });
}

function toggleAdmin(userId, isAdmin){
    fetch(`/admin/toggle_admin/${userId}`, {method:'POST'})
    .then(res=>res.json()).then(data=>{
        if(data.success) location.reload();
    });
}

// Teams
function createTeam(){
    const name = document.getElementById('new-teamname').value;
    if(!name) return alert('Enter team name');
    fetch('/admin/create_team', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({name})
    }).then(res => res.json()).then(data=>{
        if(data.success) location.reload();
        else alert(data.error);
    });
}

function deleteTeam(teamId){
    fetch(`/admin/delete_team/${teamId}`, {method:'DELETE'})
    .then(res=>res.json()).then(data=>{
        if(data.success) location.reload();
    });
}

function editTeam(teamId, currentName){
    const newName = prompt('Enter new team name:', currentName);
    if(!newName) return;
    fetch(`/admin/edit_team/${teamId}`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({name:newName})
    }).then(res=>res.json()).then(data=>{
        if(data.success) location.reload();
        else alert(data.error);
    });
}