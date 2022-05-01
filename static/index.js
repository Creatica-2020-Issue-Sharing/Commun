let searchBoxes = document.querySelectorAll('.searchResultBox')
searchBoxes.forEach((box) => box.addEventListener('click', () => {
    document.querySelector('#searchChosen').setAttribute('value', box.value)
}));

function addMoreLinks(){
    submissionForm = document.querySelector("#submissionForm");
    links = document.querySelectorAll('.link')
    lastLink = links[links.length - 1]
    labelNum = parseInt(lastLink.getAttribute('name').split('').pop()) + 1;
    let label1 = document.createElement("label")
    label1.innerText = "Link title";
    label1.setAttribute('for', 'linkTitle' + labelNum);

    let input1 = document.createElement("input")
    input1.setAttribute('type', 'text');
    input1.setAttribute('name', 'linkTitle' + labelNum)
    input1.classList.add('linkTitle')

    let label2 = document.createElement("label")
    label2.innerText = "Link";
    label2.setAttribute('for', 'link' + labelNum);

    let input2 = document.createElement("input")
    input2.setAttribute('type', 'text');
    input2.setAttribute('name', 'link' + labelNum)
    input2.classList.add('link')
    submissionForm.insertBefore(input2, document.querySelector('#submissionSubmit'))
    submissionForm.insertBefore(label2, input2)
    submissionForm.insertBefore(input1, label2)
    submissionForm.insertBefore(label1, input1)

}