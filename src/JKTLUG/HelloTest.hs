{-# OPTIONS_GHC -F -pgmF htfpp #-}

module JKTLUG.HelloTest (htf_thisModulesTests) where

import Test.Framework
import JKTLUG.Hello (greet)

test_greet =
     do assertEqual "Hello, Alice." (greet "Alice")
