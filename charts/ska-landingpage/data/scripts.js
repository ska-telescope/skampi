
const skaMid = {
  'name': 'SKA Mid',
  'image': 'https://res.cloudinary.com/dmwc3xvv8/image/upload/v1612505475/ska_mid_mnvuil.svg'
}

const skaLow = {
  'name': 'SKA Low',
  'image': 'https://res.cloudinary.com/dmwc3xvv8/image/upload/v1612505143/ska_low_dzquiv.svg'
}

const MVPInstance = (MVP === 'ska-mid') ? skaMid : (MVP === 'ska-low' ? skaLow : null)



const kibanaURL = '../app/logs/stream?' +
  'flyoutOptions=(flyoutId:!n,flyoutVisibility:hidden,surroundingLogsId:!n)&' +
  'logPosition=(end:now,position:(tiebreaker:277595,time:1612798881864),start:now-1d,streamLive:!f)&' +
  `logFilter=(expression:%27kubernetes.namespace:%20${NAMESPACE}%27,kind:kuery)`

const model = {
  'MVPInstance': MVPInstance,
  'Namespace': NAMESPACE,
  'ChartInfo': CHARTINFO,
  'KibanaURL': kibanaURL
}

let subcharts = ''
CHARTINFO.dependencies.forEach((item) => {
  subcharts += `<p>...............${item.name}-${item.version}</p>`
})

const chartInfo = `
<p><strong>Chart:</strong> ${CHARTINFO.name}-${CHARTINFO.version}</p>
<p><strong>Sub Charts:</strong></p>${subcharts}
`


function parse(str) {
  var results = [], re = /{([^}]+)}/g, text;

  while (text = re.exec(str)) {
    results.push(text[1]);
  }
  return results;
}

function pruneTree(textTree) {
  const attribute = textTree.substring(0, textTree.indexOf('.'))
  const prunedTree = textTree.substring(textTree.indexOf('.') + 1, textTree.length)
  if (attribute) {
    return [attribute, prunedTree]
  } else {
    return [prunedTree, ""]
  }
}

function drillDown(object, textTree) {
  const [attribute, prunedTree] = pruneTree(textTree)
  const value = object[attribute]
  if (prunedTree) {
    return drillDown(value, prunedTree)
  } else {
    return value
  }
}

function handleTemplateText(element) {
  console.log("in templateText")
  let text = $(element).text()
  const values = parse(text)
  values.forEach((value) => {
    let replace_value = drillDown(model, value)
    text = text.replace(`{${value}}`, replace_value)
  })
  $(element).text(text)
  $(element).removeClass('is-hidden')
}

function templateVersioning(element) {
  console.log("in templateVersioning")
  $(element).html(chartInfo)
}

function handleTemplateImage(element) {
  console.log("in templateImage")
  let source = $(element).attr('src')
  const replace_source = drillDown(model, source)
  $(element).attr('src', replace_source)
  $(element).parent().removeClass('is-hidden')
}

function handleOpenedByMenu(element) {
  const id = $(element).attr('id')
  const id_nr = id.substr(id.indexOf('_') + 1)
  const menu_item = $(`#openerfor_${id_nr}`)
  menu_item.click(() => $(element).removeClass('is-hidden'))
  $(element).find('.delete').click(() => $(element).addClass('is-hidden'))

}

function handleTemplateURL(element) {
  console.log("in handleTemplateURL")
  let url = $(element).attr('href')
  const replace_source = drillDown(model, url)
  $(element).attr('href', replace_source)
}

const template = {
  'templateText': handleTemplateText,
  'templateImage': handleTemplateImage,
  'templateVersioning': templateVersioning,
  'templateURL': handleTemplateURL,
  'openedByMenu': handleOpenedByMenu
}

$.when($.ready).then(() => {
  console.log("updating dom...");
  Object.keys(template).forEach((key) => {
    $(`.${key}`).each((index, element) => template[key](element))
  })
})