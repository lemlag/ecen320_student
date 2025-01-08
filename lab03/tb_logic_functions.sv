//////////////////////////////////////////////////////////////////////////////////
//
//  Filename: tb_logic_functions.sv
//
//////////////////////////////////////////////////////////////////////////////////

module tb_logic_functions();

	logic a,b,c;
	logic o1,o2,o3,o4;
	logic t_o1, t_o2, t_o3, t_o4;
	integer i,errors;

	// Instance the unit under test
	logic_functions dut(.A(a), .B(b), .C(c), .O1(o1), .O2(o2), .O3(o3), .O4(o4));

	initial begin

		// print time in ns (-9) with the " ns" string
		$timeformat(-9, 0, " ns", 0);
		errors = 0;
		#20
		$display("*** Starting simulation at time %t ***", $time);
		#20
		// set defaults
		a = 0;
		b = 0;
		c = 0;
		
		// Try all 8 conditions
		for(i=0; i < 8; i=i+1) begin
			#10
			a = (i & 3'b100) == 3'b100;
			b = (i & 3'b010) == 3'b010;
			c = (i & 3'b001) == 3'b001;
			#10
			$display("A=%b B=%b C=%b: O1=%b O2=%b O3=%b O4=%b at time %t", 
				a,b,c, o1, o2, o3, o4, $time);
			if (o1 != t_o1) begin
				$display(" Error: O1=%b but expecting %b", o1, t_o1);
				errors = errors + 1;
			end
			if (o2 != t_o2) begin
				$display(" Error: O2=%b but expecting %b", o2, t_o2);
				errors = errors + 1;
			end
			if (o3 != t_o3) begin
				$display(" Error: O3=%b but expecting %b", o3, t_o3);
				errors = errors + 1;
			end
			if (o4 != t_o4) begin
				$display(" Error: O4=%b but expecting %b", o4, t_o4);
				errors = errors + 1;
			end
		end

		#20
		$display("*** Simulation done with %0d errors at time %t ***", errors, $time);
		$finish;

	end // initial

	assign t_o1 = a&c | ~a&b; // AC+A'B
	assign t_o2 = (a|~c) & (b&c); // (A + ~C)(BC)
	assign t_o3 = (a & ~b) | c; // (AB') + C
	assign t_o4 = ~( ~(a & b ) & ~(~c&~b) ); // [(AB)'(C'B')]'

endmodule