function addText(event) {
    var targ = event.target || event.srcElement;
    document.getElementById("step_code").value += targ.textContent || targ.innerText;
}