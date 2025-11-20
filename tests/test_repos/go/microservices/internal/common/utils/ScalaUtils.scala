package com.greenfuze.microservices.utils

object ScalaUtils {
  def formatString(input: String): String = {
    input.trim().toLowerCase()
  }
  
  def combineStrings(str1: String, str2: String): String = {
    s"$str1-$str2"
  }
}
