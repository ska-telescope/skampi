
const skaMid = {
  'name' : 'SKA Mid',
  'image': 'https://res.cloudinary.com/dmwc3xvv8/image/upload/v1612505475/ska_mid_mnvuil.svg'
}

const skaLow = {
  'name' : 'SKA Low',
  'image': 'https://res.cloudinary.com/dmwc3xvv8/image/upload/v1612505143/ska_low_dzquiv.svg'
}

const MVPInstance = (MVP === 'mvp-mid') ? skaMid : (MVP === 'mvp-low' ? skaLow : null)

const model = {
  'MVPInstance' : MVPInstance
}

function parse(str) {
  var results = [], re = /{([^}]+)}/g, text;

  while(text = re.exec(str)) {
    results.push(text[1]);
  }
  return results;
}

function pruneTree(textTree){
  const attribute = textTree.substring(0,textTree.indexOf('.'))
  const prunedTree = textTree.substring(textTree.indexOf('.')+1,textTree.length)
  if (attribute){
    return [attribute,prunedTree]
  } else {
    return [prunedTree,""]
  } 
}

function drillDown(object,textTree){
  const [attribute,prunedTree] = pruneTree(textTree)
  const value = object[attribute]
  if (prunedTree){
    return drillDown(value,prunedTree)
  } else{
    return value
  }
}
 
function handleTemplateText(element){
  console.log("in templateText")
  let text = $(element).text()
  const values = parse(text)
  values.forEach((value)=>{
    let replace_value = drillDown(model,value)
    text = text.replace(`{${value}}`,replace_value)
  })
  $(element).text(text)
  $(element).removeClass('is-hidden')
}

function handleTemplateImage(element){
  console.log("in templateImage")
  let source = $(element).attr('src')
  const replace_source = drillDown(model,source)
  $(element).attr('src',replace_source)
  $(element).parent().removeClass('is-hidden')
}

const template = {
  'templateText': handleTemplateText,
  'templateImage': handleTemplateImage,
}

$.when( $.ready ).then(()=> {
  console.log("updating dom...");
  Object.keys(template).forEach((key)=>{
    $(`.${key}`).each((index,element)=>template[key](element))
  })
})