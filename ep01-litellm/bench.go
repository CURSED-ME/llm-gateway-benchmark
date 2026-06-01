package main

import (
	"fmt"
	"time"
	"github.com/pkoukk/tiktoken-go"
)

func main() {
	start := time.Now()
	for i := 0; i < 100; i++ {
		_, err := tiktoken.GetEncoding("cl100k_base")
		if err != nil {
			panic(err)
		}
	}
	fmt.Printf("100 GetEncoding calls took %v\n", time.Since(start))
}
