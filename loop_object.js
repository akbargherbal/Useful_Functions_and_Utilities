/* 
Given object dict_1; loop through the object and print the key and value of the object
*/

const dict_1 = {
    "name": "John",
    "age": 30,
    "city": "New York"
};

for (const [key, value] of Object.entries(dict_1)) {
    console.log(`key: ${key} value: ${value}`);
}

// Output
/* 
key: name value: John
key: age value: 30
key: city value: New York
*/