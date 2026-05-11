{-# OPTIONS_GHC -F -pgmF htfpp #-}

module Main where

import Test.Framework
import {-@ HTF_TESTS @-} JKTLUG.HelloTest
import {-@ HTF_TESTS @-} JKTLUG.MediaWikiTest

main :: IO ()
main = htfMain htf_importedTests
