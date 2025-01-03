// binary_adder.sv
//
// Perform binary addition on two 2-bit signals to produce a 3-bit output.
//
// switches sw[1:0] are the first two-bit binary input
// switches sw[3:2] are the second two-bit binary input
//
// The result is a 3-bit number that is displayed on the LEDs led[2:0]


module binary_adder (
        input logic [3:0] sw,   // First four switches for input
        output logic [2:0] led  // First three LEDs for output
    );
    logic [2:0] carry;          // Carry signals

    // Bit 0
    xor(led[0], sw[0], sw[2]);                      // sum[0]
    and(carry[0], sw[0], sw[2]);                    // carry[0]
    // Bit 1
    xor(led[1], sw[1], sw[3]);                      // sum[1]
    and(a_and_b, sw[1], sw[3]);
    and(a_and_c, sw[1], carry[0]);
    and(b_and_c, sw[3], carry[0]);
    or(carry[1], a_and_b, a_and_c, b_and_c);        // carry[1]
    // Bit 3
    buf(led[2], carry[1]);                  

endmodule
