{-# OPTIONS_GHC -F -pgmF htfpp #-}

module JKTLUG.MediaWikiTest (htf_thisModulesTests) where

import Test.Framework
import JKTLUG.MediaWiki
import JKTLUG.Parser (runParser, char)
import Control.Applicative

test_parserApp = do
    assertEqual
        ('a','y')
        $ runParser ((\a b -> (a,b)) <$> char <*> char) "ay"
    assertEqual
        ('a','y')
        $ runParser (liftA2 (\a b -> (a,b)) char char) "ay"

test_parserMonad =
    let parser = do a <- char
                    b <- char
                    return (a,b)
    in assertEqual ('a','y') $ runParser parser "ay"

test_parse = do
    assertEqual
        []
        $ parsePage ""
    assertEqual
        [Markup "abc"]
        $ parsePage "abc"
    assertEqual
        [Transclude "trans:a b" []]
        $ parsePage "{{trans:a b}}"
    assertEqual
        [Markup "** ", Transclude "w:ja" [(Nothing,"user:name")]]
        $ parsePage "** {{w:ja|user:name}}"
    assertEqual
       [Markup "inc", NoInclude [Markup "noinc", NoInclude [Markup "doublenoinc"]]]
        $ parsePage "inc<noinclude>noinc<noinclude>doublenoinc</noinclude></noinclude>"
    assertEqual
        [ Markup "begin"
        , Transclude "trans"
            [ (Nothing,"value1"), (Nothing,""), (Just "name2","value2") ]
        , NoInclude
          [ Transclude "t2" []
          , Markup "end"
          ]
        ]
        $ parsePage  $ "begin{{trans|value1||name2=value2}}"
                    ++ "<noinclude>{{t2}}end</noinclude>"
    assertEqual
        [Markup "{{{p}}}{{{{}}}}{}"]
        $ parsePage "{{{p}}}{{{{}}}}{}"

    assertEqual
        [Transclude "ML2" [ (Nothing,"0803/msg00500.html"), (Nothing,"Dave Brown") ]]
        $ parsePage "{{ML2|0803/msg00500.html|Dave Brown}}"

    assertEqual
        [Redirect "Link", Markup "content"]
        $ parsePage "#REDIRECT [[Link]]content"

test_noinclude = do
    assertEqual
        [Markup "visible ", NoInclude [Markup "hidden"]]
        $ parsePage "visible <noinclude>hidden</noinclude>"

