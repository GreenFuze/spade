use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn process_data(data: Vec<i32>) -> Vec<i32> {
    data.iter().map(|x| x * 2).collect()
}
