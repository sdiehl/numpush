; ModuleID = 'haskell_codegen.o'

define internal cc10 i32 @plus(i32, i32) {
_L1:
  %2 = add i32 %0, %1
  ret i32 %2
}

define i32 @test(i32, i32) {
_L1:
  %2 = add i32 %0, %1
  ret i32 %2
}
