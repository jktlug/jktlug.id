# Haskell Basics for TLUG Website Development

This guide covers the Haskell concepts and patterns you need to
understand in order to work on the TLUG website. It is not a
general Haskell tutorial — it focuses on what you'll encounter in
this codebase.

## Prerequisites

You should be able to:
- Read basic Haskell syntax (functions, types, `let`/`where`)
- Build the project with `./Test` or `stack build`
- Find and read source files in `app/` and `src/`

## 1. The Core Pattern: Parser Combinators

The most important concept in this codebase is **parser
combinators**. `TLUG.Parser` is a tiny parser library built from
scratch. Everything is a `Parser a` — a function that takes a
`String` and either succeeds (returning a value and the remaining
string) or fails.

### The Type

```haskell
data ParserState = ParserState { remaining :: String }
newtype Parser a = Parser { parse :: ParserState -> Maybe (a, ParserState) }
```

- `ParserState` holds the input text we haven't consumed yet.
- `Parser a` is a function: given state, return `Just (value, newState)`
  or `Nothing` if parsing fails.

### The Functor Instance

```haskell
instance Functor Parser where
    fmap f (Parser parse) =
        Parser $ \state ->
            case parse state of
                Nothing -> Nothing
                Just (x, state') -> Just (f x, state')
```

If the inner parser succeeds, apply `f` to its result. This is how
you transform parsed values.

### The Applicative Instance

```haskell
instance Applicative Parser where
    pure x = Parser $ \state -> Just (x, state)
    (Parser parse1) <*> parser2 =
        Parser $ \state -> case parse1 state of
            Nothing -> Nothing
            Just (f, state') -> parse (fmap f parser2) state'
```

- `pure x` — a parser that always succeeds with value `x` without
  consuming input.
- `p1 <*> p2` — run `p1` to get a function, then run `p2` on the
  remaining text and apply the function. This is the key to
  **sequencing parsers**.

**Why Applicative matters:** You use it to write things like:

```haskell
Transclude <$> string "{{" <*> pageName <*> params <*> string "}}"
```

This says: parse `"{{"`, then parse a page name, then parse params,
then parse `"}}"`, and combine all four results into a `Transclude`
value.

### The Alternative Instance

```haskell
instance Alternative Parser where
    empty = Parser $ return Nothing
    p1 <|> p2 = Parser $ \state ->
        case parse p1 state of
            Nothing -> parse p2 state
            x -> x
```

- `empty` — a parser that always fails.
- `p1 <|> p2` — try `p1`; if it fails, try `p2` at the **same
  position** (does not consume input on failure). This is "choice".

**This is how `chunk` tries different things:**

```haskell
chunk :: Parser Chunk
chunk = markup <|> transclude <|> noInclude <|> redir
```

Try to parse markup. If that fails, try transclusion. If that
fails, try `<noinclude>` ... and so on.

### The Monad Instance

```haskell
instance Monad Parser where
    parser >>= k = Parser $ \state ->
        case (parse parser) state of
            Nothing -> Nothing
            Just (x, state') -> parse (k x) state'
```

- `p >>= f` — run parser `p`; if it succeeds with value `x`, run
  `f x` to get a new parser, then run that on the remaining text.

Monads let you use **do-notation** when you need to use intermediate
results to decide what to parse next:

```haskell
doTransclude par top (Transclude{..}:xs) = ...
```

But most of this codebase prefers Applicative style (`<*>`) because
it composes more cleanly.

## 2. Pattern: Parsing with Applicative Operators

The operators you will see everywhere:

| Operator | Meaning | Example |
|---|---|---|
| `f <$> p1 <*> p2` | Apply `f` to results of `p1` and `p2` | `Transclude <$> name <*> params` |
| `p1 <* p2` | Run `p1` and `p2`, return `p1`'s result | `Transclude <* string "{{"` |
| `p1 *> p2` | Run `p1` and `p2`, return `p2`'s result | `string "{{" *> name` |
| `p1 <*> p2` | Sequence parsers, apply function | See above |
| `p1 \|> p2` | Try `p1`, else `p2` | `markup \|> transclude` |
| `many p` | Zero or more repetitions of `p` | `many chunk` |
| `some p` | One or more repetitions of `p` | `some char` |
| `optional p` | Zero or one of `p` | `optional (string "\|+")` |

### Example from the Codebase

```haskell
-- Parse a transclude: {{Name|param1|param2=value}}
transclude :: Parser Chunk
transclude = Transclude <$
    numBraces (== 2) <*>                       -- consume {{
    some (anyExcept [transEnd, "|", "\n"]) <*  -- page name
    many (anyExcept [transEnd, "|"]) <*>       -- skip to |
    many param <*
    string transEnd                             -- consume }}
```

## 3. Record Wildcards and Pattern Matching

The code uses `RecordWildCards` extensively:

```haskell
doTransclude par top (Transclude{..}:xs) = ...
```

This brings all fields of `Transclude` into scope as variables:
`pageName` and `params`. It's shorthand for:

```haskell
doTransclude par top (Transclude pageName params:xs) = ...
```

## 4. Type Synonyms and Newtypes

```haskell
type Page = [Chunk]        -- Page is just a list of Chunks

data Chunk = Markup String
           | Transclude { pageName :: String, params :: [Param] }
           | ...
```

- `type` creates a synonym (alias). `Page` is just `[Chunk]`.
- `data` creates a new type with constructors. `Chunk` can be markup,
  a transclude, etc.

## 5. Maybe and Null Handling

Haskell uses `Maybe a` instead of null:

```haskell
data Maybe a = Nothing | Just a
```

Functions for working with Maybe:

```haskell
isJust :: Maybe a -> Bool          -- True if Just
isNothing :: Maybe a -> Bool       -- True if Nothing
fromJust :: Maybe a -> a            -- Unwrap Just (crash if Nothing!)
maybe :: b -> (a -> b) -> Maybe a -> b  -- Safe unwrapping with default
```

Example from `SiteCompiler.hs`:

```haskell
tcredir <- unsafeCompiler $ redirect <$> parse
if isJust tcredir
    then return $ Item ... (makeRedir (fromJust tcredir) tcmarkup)
    else ...
```

## 6. IO and unsafeCompiler

Hakyll's `Compiler` monad is pure by default. To run IO (like
reading files from disk, which `parseFile` does for transclusion), you
need `unsafeCompiler`:

```haskell
tcmarkup <- unsafeCompiler $ body <$> parse
```

This lifts an `IO a` action into the `Compiler a` context. The
"unsafe" is because it breaks Hakyll's ability to track
dependencies for incremental rebuilds.

## 7. The Hakyll Concepts

### Rules

`hakyll $ do ...` declares all the rules the compiler knows about.

### match

```haskell
match "docroot/*.html" $ do
    route   dropInitialComponent
    compile $ pandocCompiler >>= loadAndApplyTemplate ...
```

- `match "pattern"` — matches source files by glob pattern.
- `route` — determines the output path.
- `compile` — defines the transformation pipeline.

### Item a

Hakyll represents a file as an `Item a`:

```haskell
Item { itemIdentifier :: Identifier, itemBody :: a }
```

- `itemIdentifier` is the source file path.
- `itemBody` is the parsed/processed content.

### Context

A `Context a` is a way to make variables available in templates.
`defaultContext` provides things like `$title$`, `$url$`, etc. You
can compose contexts with `mappend` (or `<>`):

```haskell
constField "title" "Archives" <> defaultContext
```

### Templates

Templates use `$variable$` syntax. The `$body$` variable is special:
it's the rendered content of the inner item. In `main.html`:

```html
<div class="content">
  $body$
</div>
```

The content being wrapped is substituted here.

## 8. Basic Syntax You'll Encounter

### String Literals and OverloadedStrings

`{-# LANGUAGE OverloadedStrings #-}` allows string literals to be
other types (like `Data.Text` or Hakyll's internal path types).

### List Comprehensions and Map

```haskell
map (\a -> if a == ' ' then '_' else a) pageName
-- Or with sections:
map toLower "Hello"  -- "hello"
```

### Where Clauses

```haskell
read ropt item =
    case ... of
        Left err    -> fail ...
        Right item' -> return item'
  where
    ropt = defaultHakyllReaderOptions
```

Local definitions at the end of a function, scoped to that function.

### Lambda Expressions

```haskell
\a -> if a == ' ' then '_' else a
```

An anonymous function. Equivalent to `let f a = if a == ... in f`.

## 9. Compilation Model

The site uses [Stack](https://docs.haskellstack.org/) for builds:

- `stack.yaml` — pins the compiler version via `snapshot: lts-23.27`
- `tlug-website.cabal` — declares the package, executables, modules,
  and dependencies
- `stack build` — compiles everything (downloads deps if needed)
- `stack exec site-compiler build` — runs the site compiler
- `stack exec site-compiler rebuild` — force full rebuild
- `stack exec site-compiler watch` — preview server with auto-rebuild

Dependencies are specified in the `.cabal` file:

```
build-depends: base >= 4.7 && < 5,
               hakyll,
               filepath, directory, text, pandoc, mtl
```

## Cheat Sheet: Reading This Codebase

When you see this | It means
---|---
`p1 <*> p2` | Run p1 then p2, combine results
`p1 <* p2` | Run both, keep p1's result
`p1 *> p2` | Run both, keep p2's result
`f <$> p` | Apply f to parser result
`p1 \|> p2` | Try p1, fallback to p2
`many p` | Zero or more of p
`some p` | One or more of p
`pure x` | Parser that always returns x
`return x` | Same as `pure` in IO/Compiler
`>>=` | Sequence monadic actions
`\x -> ...` | Anonymous function
`let x = y in z` | Local binding
`where x = y` | Local binding (after function body)
`f <$> io` | `fmap f io` — apply f inside functor
`item >>= f` | Chain operations on items
`loadAndApplyTemplate "template/main.html" ctx item` | Wrap content in template

## Where to Learn More

- [Hakyll Tutorial](https://jaspervdj.be/hakyll/tutorials/01-installation.html)
- [Hakyll Module Zoo Guide](https://jaspervdj.be/hakyll/tutorials/a-guide-to-the-hakyll-module-zoo.html)
- [Pandoc Manual](https://pandoc.org/MANUAL.html)
- [Haskell Programming from First Principles](http://haskellbook.com/) (comprehensive)
- [Learn You a Haskell](http://learnyouahaskell.com/) (free online, gentler)
