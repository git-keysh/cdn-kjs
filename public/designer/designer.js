const canvas=new fabric.Canvas("designer")

canvas.setWidth(210)
canvas.setHeight(320)

const shirt=document.getElementById("shirtImage")

document.querySelectorAll(".colors img").forEach(img=>{
img.onclick=()=>{
shirt.src=img.dataset.shirt
}
})

document.getElementById("addText").onclick=()=>{
const text=new fabric.IText("Text",{
left:50,
top:50,
fill:"#000"
})
canvas.add(text)
canvas.setActiveObject(text)
}

document.getElementById("drawBtn").onclick=()=>{
canvas.isDrawingMode=!canvas.isDrawingMode
}

document.getElementById("uploadBtn").onclick=()=>{
document.getElementById("imageUpload").click()
}

document.getElementById("imageUpload").onchange=e=>{
const file=e.target.files[0]
if(!file)return

const reader=new FileReader()

reader.onload=f=>{

fabric.Image.fromURL(
f.target.result,
img=>{
img.scaleToWidth(120)
canvas.add(img)
}
)

}

reader.readAsDataURL(file)
}

document.getElementById("downloadPNG").onclick=()=>{

const link=document.createElement("a")

link.href=canvas.toDataURL({
format:"png",
quality:1
})

link.download="design.png"

link.click()

}

document.getElementById("downloadPDF").onclick=()=>{

const {jsPDF}=window.jspdf

const pdf=new jsPDF()

pdf.addImage(
canvas.toDataURL("image/png"),
"PNG",
10,
10,
180,
180
)

pdf.save("design.pdf")

}