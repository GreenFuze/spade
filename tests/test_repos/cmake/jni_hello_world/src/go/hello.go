package main

import "C"
import "fmt"

//export HelloGo
func HelloGo() {
	fmt.Println("Hello from Go!")
}

func main() {}
