package testhelper

import "github.com/stretchr/testify/assert"

func AssertEqual(expected, actual interface{}) bool {
	return assert.Equal(nil, expected, actual)
}
