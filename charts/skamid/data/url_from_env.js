'use strict';
const v = TEMP;
const v2 = TEMP2;

const e = React.createElement
function URLFromEnv(props) {
    const children = props.children
    return e(
      'a',
      null,
      children
    );
}

document.querySelectorAll('.react_url_from_env')
  .forEach(domContainer => {
    const child_text = domContainer.childNodes[0].data
    ReactDOM.render(
      e(URLFromEnv,null,child_text),
      domContainer
    );
  });