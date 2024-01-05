// SPDX-License-Identifier: MIT
pragma solidity ^0.8.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

// 0x1111111254EEB25477B68fb85Ed929f73A960582   1INCH V5 Agg SC.
contract OneInchSwapProxy is Ownable {

    struct SwapDescription {
        IERC20 srcToken;
        IERC20 dstToken;
        address srcReceiver;
        address dstReceiver;
        uint256 amount;
        uint256 minReturnAmount;
        uint256 flags;
        bytes permit;
    }

    address immutable AGGREGATION_ROUTER_V5;
    address immutable initial_owner;

    constructor(address router, address initialOwner) Ownable(initialOwner) {
        AGGREGATION_ROUTER_V5 = router;
        initial_owner = initial_owner;
    }

    function swap(uint minOut, bytes calldata _data) external onlyOwner {
        (, SwapDescription memory desc, bytes memory _d) = abi.decode(_data[4:], (address, SwapDescription, bytes));

        IERC20(desc.srcToken).transferFrom(msg.sender, address(this), desc.amount);
        IERC20(desc.srcToken).approve(AGGREGATION_ROUTER_V5, desc.amount);

        (bool succ, bytes memory responseData) = address(AGGREGATION_ROUTER_V5).call(_d);
        if (succ) {
            (uint returnAmount,) = abi.decode(responseData, (uint, uint));
            require(returnAmount >= minOut);
            IERC20(desc.dstToken).transfer(msg.sender, returnAmount);
        } else {
            revert("Swap failed");
        }
    }
}
