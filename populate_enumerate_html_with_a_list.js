/* 
The equivalent of the following Python code:
dict_01 = {1: '01_EN_NOUN_AV 16NOV2022', 2: '02_EN_VERB_AV 16NOV2022', 3: '03_AR_UN_CORPUS 16NOV2022'}
list_01 = []
for k,v in dict_01.items():
    list_01.append(f'''
<form  class="quiz_selection" method="post" action="/">
    <input type="hidden" name="request_quiz_name" value={k}>
    <button type="submit" class="btn btn-outline-primary bth_quiz_selec">{v}</button>
</form>
''')
*/

var dict_01 = {1: '01_EN_NOUN_AV 16NOV2022', 2: '02_EN_VERB_AV 16NOV2022', 3: '03_AR_UN_CORPUS 16NOV2022'};
var list_01 = [];
for (const [k, v] of Object.entries(dict_01)) {
    list_01.push(`
<form  class="quiz_selection" method="post" action="/">
    <input type="hidden" name="request_quiz_name" value=${k}>
    <button type="submit" class="btn btn-outline-primary bth_quiz_selec">${v}</button>
</form>
`.trim());
}

